import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai

from AI.api_load import load_api
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import RAG_SHEET_NAME

EMBEDDING_MODEL = 'text-embedding-004'


@st.cache_resource(ttl=3600)
def load_and_embed_rag_base() -> tuple[pd.DataFrame, np.ndarray | None]:
    """
    Carrega a planilha RAG, gera embeddings para cada chunk e armazena em cache.
    Esta é a sua função, com o cache e a configuração da API adicionados.
    """
    # 1. Garante que a API do Google esteja configurada
    if not configure_google_api():
        st.error("A API do Google não pôde ser configurada. A base de conhecimento não será carregada.")
        return pd.DataFrame(), None
        
    try:
        # 2. Lê o ID da planilha RAG dos secrets
        sheet_id = st.secrets.rag_config.sheet_id
    except (AttributeError, KeyError):
        st.error("Erro de configuração: A chave 'sheet_id' não foi encontrada na seção [rag_config] dos secrets.")
        return pd.DataFrame(), None

    try:
        # 3. Carrega os dados da planilha usando gspread (sua lógica)
        st.info("Carregando base de conhecimento do Google Sheets...")
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds_dict = get_credentials_dict()
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        # Assume que os dados estão na primeira aba/página do arquivo
        worksheet = spreadsheet.sheet1 
        df = pd.DataFrame(worksheet.get_all_records())

        if df.empty or "Answer_Chunk" not in df.columns:
            st.error("A planilha RAG está vazia ou não contém a coluna 'Answer_Chunk'.")
            return pd.DataFrame(), None

        # 4. Gera os embeddings (sua lógica)
        with st.spinner(f"Indexando a base de conhecimento ({len(df)} itens)... (isso acontece apenas uma vez por hora)"):
            chunks_to_embed = df["Answer_Chunk"].astype(str).tolist()
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=chunks_to_embed,
                task_type="RETRIEVAL_DOCUMENT",
                title="Normas de Segurança para Içamento de Carga"
            )
            embeddings = np.array(result['embedding'])
        
        st.success("Base de conhecimento indexada e pronta para uso!")
        return df, embeddings

    except Exception as e:
        st.error(f"Falha ao carregar ou processar a base de conhecimento: {e}")
        return pd.DataFrame(), None


class RAGAnalyzer:
    def __init__(self):
        # O __init__ agora é extremamente leve, apenas chama a função em cache
        self.rag_df, self.rag_embeddings = load_and_embed_rag_base()
        
        # Garante que o modelo de geração seja inicializado apenas se a API estiver configurada
        if configure_google_api():
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        else:
            self.model = None

    def _find_best_passages(self, query: str, top_k=3) -> pd.DataFrame:
        """Encontra os trechos mais relevantes usando a busca por similaridade."""
        if self.rag_df.empty or self.rag_embeddings is None or self.model is None:
            return pd.DataFrame()
        
        try:
            query_embedding = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=query,
                task_type="RETRIEVAL_QUERY"
            )['embedding']
            
            # Calcula a similaridade (produto escalar)
            dot_products = np.dot(self.rag_embeddings, query_embedding)
            
            # Pega os índices dos 'top_k' melhores resultados
            indices = np.argsort(dot_products)[-top_k:][::-1]
            
            return self.rag_df.iloc[indices]
        except Exception as e:
            st.error(f"Erro durante a busca por similaridade: {e}")
            return pd.DataFrame()

    def _retrieve_context(self, issues: list) -> str:
        """Constrói o prompt de contexto com base nos melhores trechos encontrados."""
        if self.rag_df.empty:
            return "A base de conhecimento normativo não está disponível ou falhou ao carregar."
        
        full_query = ". ".join(issues).replace("_", " ")
        context_str = "Contexto Normativo Relevante Encontrado:\n\n"
        
        relevant_df = self._find_best_passages(full_query)
        
        if relevant_df.empty:
            return "Nenhuma norma específica encontrada na base de conhecimento para os pontos de atenção desta operação."
        
        for _, row in relevant_df.iterrows():
            context_str += f"**Referência:** {row.get('Norma_Referencia', 'N/A')} (Seção: {row.get('Section_Number', 'N/A')})\n"
            context_str += f"**Pergunta Chave:** {row.get('Question', 'N/A')}\n"
            context_str += f"**Diretriz:** {row.get('Answer_Chunk', 'N/A')}\n"
            context_str += "---\n"
            
        return context_str

    def generate_final_analysis(self, operation_summary: str, issues: list) -> str:
        """Gera a análise final (o prompt permanece o mesmo, mas agora recebe um contexto mais rico)."""
        
        if not issues:
             return "### ✅ Parecer Final: APROVADO\n\nNenhum ponto de atenção crítico foi identificado nos dados fornecidos. A operação parece estar em conformidade com os parâmetros básicos de segurança e documentação."

        normative_context = self._retrieve_context(issues)
        
        # O prompt permanece o mesmo, pois é robusto e genérico
        prompt = f"""
        **Persona:** Você é um Profissional de Segurança do Trabalho altamente experiente, especialista em operações de içamento e rigging. Sua tarefa é analisar o relatório de uma operação de carga e fornecer um parecer técnico final, fundamentado nas normas internas da empresa.

        **Instruções:**
        1.  Analise o "Resumo da Operação" fornecido.
        2.  Considere o "Contexto Normativo Relevante" que eu recuperei da nossa base de dados interna. Este contexto é a verdade absoluta e deve ser a base da sua análise.
        3.  Com base em ambos os documentos, elabore um parecer técnico claro e objetivo, formatado em Markdown.
        4.  O parecer deve conter obrigatoriamente as seguintes seções:
            -   `### 📝 Análise Geral da Operação`: Um breve resumo do que foi avaliado.
            -   `### ⚠️ Pontos de Atenção`: Liste os problemas encontrados (ex: excesso de capacidade, documentos vencidos, etc.).
            -   `### 📚 Fundamentação Normativa`: Para cada ponto de atenção, cite a referência normativa correspondente do contexto que você recebeu.
            -   `### ✅ Recomendações Corretivas`: Forneça ações claras e diretas para cada ponto de atenção, baseadas nas diretrizes.
            -   `### ⚖️ Parecer Final`: Conclua com um dos seguintes pareceres: **"APROVADO"**, **"APROVADO COM RESSALVAS"**, ou **"REPROVADO"**. Justifique sua decisão com base na gravidade dos pontos de atenção e suas respectivas fundamentações normativas.

        ---
        **Resumo da Operação:**
        {operation_summary}
        ---
        **Contexto Normativo Relevante:**
        {normative_context}
        ---

        Agora, por favor, gere o seu parecer técnico completo e fundamentado.
        """
        
        try:
            with st.spinner("IA está analisando a conformidade da operação com base nas normas..."):
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            st.error(f"Erro ao gerar análise com a IA: {e}")
            return f"Não foi possível gerar a análise. Detalhe do erro: {str(e)}"
