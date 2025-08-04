import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai

from AI.api_load import load_api
from gdrive.gdrive_upload import GoogleDriveUploader

RAG_SHEET_NAME = "RAG_PIP"
EMBEDDING_MODEL = 'text-embedding-004'

class RAGAnalyzer:
    def __init__(self):
        load_api()
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
        self.knowledge_base_df = self._load_and_embed_knowledge_base()

    @st.cache_data(ttl=3600)  # Cache por 1 hora para evitar recarregar e re-embedar constantemente
    def _load_and_embed_knowledge_base(_self):
        """
        Carrega a base de conhecimento da planilha Google, cria um documento sintético
        para cada linha e gera os embeddings em tempo real.
        Os resultados são armazenados em cache para performance.
        """
        try:
            # 1. Carregar dados do Google Sheets
            uploader = GoogleDriveUploader()
            st.info(f"Carregando e processando a base de conhecimento '{RAG_SHEET_NAME}'...")
            data = uploader.get_data_from_sheet(RAG_SHEET_NAME)
            
            if not data or len(data) < 2:
                st.warning(f"A base de conhecimento '{RAG_SHEET_NAME}' está vazia ou não foi encontrada.")
                return pd.DataFrame()

            headers = data[0]
            df = pd.DataFrame(data[1:], columns=headers)
            
            # 2. Criar o documento sintético para embedding
            # Combinamos as colunas mais ricas em texto para criar um super-documento.
            # Isso cria um vetor que representa o conceito completo daquela linha.
            required_cols = ['Keywords', 'Question', 'Answer_Chunk']
            if not all(col in df.columns for col in required_cols):
                 st.error(f"A base de conhecimento está mal formatada. Faltam as colunas: {', '.join(col for col in required_cols if col not in df.columns)}")
                 return pd.DataFrame()
            
            df['synthetic_document'] = (
                "Palavras-chave: " + df['Keywords'].fillna('') + "; " +
                "Pergunta Relevante: " + df['Question'].fillna('') + "; " +
                "Diretriz ou Resposta: " + df['Answer_Chunk'].fillna('')
            )
            
            texts_to_embed = df['synthetic_document'].tolist()
            
            # 3. Gerar Embeddings em tempo real
            st.info(f"Gerando embeddings para {len(df)} normas...")
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=texts_to_embed,
                task_type="RETRIEVAL_DOCUMENT",
                title="Normas de Segurança para Içamento de Carga"
            )
            df['embedding'] = result['embedding']
            st.success("Base de conhecimento pronta para uso.")
            return df
        
        except Exception as e:
            st.error(f"Falha ao carregar e processar a base de conhecimento: {e}")
            return pd.DataFrame()

    def _find_best_passages(self, query: str, top_k=3) -> pd.DataFrame:
        """Encontra os trechos mais relevantes no DataFrame usando similaridade de embeddings."""
        if self.knowledge_base_df.empty or 'embedding' not in self.knowledge_base_df.columns:
            return pd.DataFrame()

        # 1. Gera o embedding para a consulta (o problema)
        query_embedding = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )['embedding']
        
        # 2. Calcula a similaridade (produto escalar)
        dot_products = np.dot(np.stack(self.knowledge_base_df['embedding']), query_embedding)
        
        # 3. Pega os índices dos 'top_k' melhores resultados
        indices = np.argsort(dot_products)[-top_k:][::-1]
        
        return self.knowledge_base_df.iloc[indices]

    def _retrieve_context(self, issues: list) -> str:
        """
        Busca na base de conhecimento os trechos mais relevantes para os problemas identificados
        usando a busca por similaridade de vetores.
        """
        if self.knowledge_base_df.empty:
            return "A base de conhecimento normativo não está disponível."
        
        # Concatena todos os problemas em uma única consulta
        full_query = ". ".join(issues).replace("_", " ") # Transforma 'cnh_vencida' em 'cnh vencida'
        
        context_str = "Contexto Normativo Relevante Encontrado:\n\n"
        
        relevant_df = self._find_best_passages(full_query)
        
        if relevant_df.empty:
            return "Nenhuma norma específica encontrada na base de conhecimento para os pontos de atenção desta operação."
        
        for _, row in relevant_df.iterrows():
            # Agora podemos incluir todas as informações que quisermos no contexto
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
        **Persona:** Você é um Engenheiro de Segurança do Trabalho altamente experiente, especialista em operações de içamento e rigging. Sua tarefa é analisar o relatório de uma operação de carga e fornecer um parecer técnico final, fundamentado nas normas internas da empresa.

        **Instruções:**
        1.  Analise o "Resumo da Operação" fornecido.
        2.  Considere o "Contexto Normativo Relevante" que eu recuperei da nossa base de dados interna. Este contexto é a verdade absoluta e deve ser a base da sua análise.
        3.  Com base em ambos os documentos, elabore um parecer técnico claro e objetivo, formatado em Markdown.
        4.  O parecer deve conter obrigatoriamente as seguintes seções:
            -   `### 📝 Análise Geral da Operação`: Um breve resumo do que foi avaliado.
            -   `### ⚠️ Pontos de Atenção`: Liste os problemas encontrados (ex: excesso de capacidade, documentos vencidos, etc.).
            -   `### 📚 Fundamentação Normativa`: Para cada ponto de atenção, cite a diretriz e a referência normativa correspondente do contexto que você recebeu.
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
