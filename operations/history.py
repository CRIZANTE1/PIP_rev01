import streamlit as st
import pandas as pd
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from operations.plot import criar_diagrama_guindaste # Importar a função do gráfico

@st.cache_data(ttl=600)
def load_sheet_data(sheet_name):
    """
    Carrega dados de uma aba específica do Google Sheets e os converte em um DataFrame.
    """
    try:
        uploader = GoogleDriveUploader()
        data = uploader.get_data_from_sheet(sheet_name)
        
        if not data or len(data) < 2:
            st.warning(f"A planilha '{sheet_name}' está vazia ou não foi encontrada.")
            return pd.DataFrame()
            
        headers = data[0]
        rows = data[1:]
        
        max_cols = len(headers)
        cleaned_rows = []
        for row in rows:
            cleaned_row = row[:max_cols] + [None] * (max_cols - len(row))
            cleaned_rows.append(cleaned_row)
            
        df = pd.DataFrame(cleaned_rows, columns=headers)
        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha '{sheet_name}': {e}")
        return pd.DataFrame()

def make_urls_clickable(df):
    """Transforma colunas que contêm URLs em links HTML clicáveis para a visão geral."""
    for col in df.columns:
        if "URL" in col.upper() or "LINK" in col.upper():
            df[col] = df[col].apply(lambda x: f'<a href="{x}" target="_blank">Abrir Link</a>' if pd.notna(x) and str(x).startswith('http') else "N/A")
    return df

def render_document_status(dados_guindauto):
    """
    Renderiza uma lista de documentos com ícones de status (✅/❌) e links.
    """
    st.subheader("Documentos Avaliados")

    # CORREÇÃO CRÍTICA: Os nomes das colunas aqui foram alterados para um padrão mais provável,
    # que deve corresponder EXATAMENTE aos cabeçalhos da sua planilha de "Informações do Guindauto".
    doc_map = {
        "ART (Anot. Resp. Técnica)": "URL ART",
        "Certificado NR-11": "URL NR-11",
        "CNH do Operador": "URL CNH",
        "CRLV do Veículo": "URL CRLV",
        "Manutenção Preventiva": "URL M_PREV",
        "Gráfico de Carga": "URL Gráfico de Carga"
    }

    for doc_name, col_name in doc_map.items():
        # .get(col_name) procura pela coluna com o nome EXATO.
        url = dados_guindauto.get(col_name)

        if pd.notna(url) and str(url).strip().startswith('http'):
            st.markdown(f"✅ **{doc_name}**: <a href='{url}' target='_blank'>Abrir Documento</a>", unsafe_allow_html=True)
        else:
            st.markdown(f"❌ **{doc_name}**: Documento não fornecido")

def safe_to_numeric(series):
    """
    Converte uma série para numérico de forma segura, tratando vírgulas como decimais.
    """
    if series is None:
        return None
    return pd.to_numeric(str(series).replace(',', '.'), errors='coerce')

def render_diagrama(dados_icamento):
    """
    Renderiza o diagrama de içamento a partir dos dados históricos.
    """
    st.subheader("Diagrama da Operação")
    
    try:
        # Os nomes aqui são da planilha de "Dados de Içamento"
        raio_max = safe_to_numeric(dados_icamento.get('Raio Máximo (m)'))
        alcance_max = safe_to_numeric(dados_icamento.get('Alcance Máximo (m)'))
        carga_total = safe_to_numeric(dados_icamento.get('Carga Total (kg)'))
        capacidade_raio = safe_to_numeric(dados_icamento.get('Capacidade Raio (kg)'))
        angulo_minimo = safe_to_numeric(dados_icamento.get('Ângulo Mínimo da Lança'))
        
        # Se qualquer um dos valores essenciais estiver vazio na planilha, esta condição falhará.
        if all(pd.notna([raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo])):
            fig = criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não foi possível gerar o diagrama. Dados insuficientes ou inválidos no registro.")
    
    except Exception as e:
        st.error(f"Ocorreu um erro ao renderizar o diagrama: {e}")


def show_history_page():
    st.title("Histórico de Avaliações")
    st.info("Os dados são atualizados a cada 10 minutos. Para forçar a atualização, limpe o cache.")
    
    if st.button("Limpar Cache e Recarregar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Carregando dados das planilhas..."):
        df_lifting = load_sheet_data(LIFTING_SHEET_NAME)
        df_crane = load_sheet_data(CRANE_SHEET_NAME)

    if df_lifting.empty or df_crane.empty:
        st.warning("Não foi possível carregar os dados do histórico. Verifique se ambas as planilhas (içamento e guindauto) estão preenchidas.")
        return

    st.subheader("Buscar e Analisar Avaliação por ID")
    id_column = df_lifting.columns[0]
    
    search_id = st.text_input("Digite o ID da Avaliação (ex: AV20240101-abcdefgh)", key="search_id_input")

    if st.button("Buscar por ID", key="search_button") and search_id:
        st.markdown("---")
        
        result_lifting = df_lifting[df_lifting[id_column] == search_id]
        result_crane = df_crane[df_crane.iloc[:, 0] == search_id] # Busca pelo ID na primeira coluna da aba do guindaste

        if not result_lifting.empty and not result_crane.empty:
            dados_icamento = result_lifting.iloc[0]
            dados_guindauto = result_crane.iloc[0]

            st.header(f"Análise Detalhada da Avaliação: {search_id}")

            col1, col2 = st.columns([2, 1])

            with col1:
                render_diagrama(dados_icamento)

            with col2:
                st.subheader("Principais Indicadores")
                
                carga_total_val = safe_to_numeric(dados_icamento.get('Carga Total (kg)', 0))
                st.metric("Carga Total da Operação", f"{carga_total_val:,.2f} kg".replace(",", "."))
                
                st.metric("Utilização no Raio", dados_icamento.get('% Utilização Raio', 'N/A'))
                st.metric("Utilização na Lança", dados_icamento.get('% Utilização Alcance', 'N/A'))
                
                adequado = dados_icamento.get('Adequado')
                if str(adequado).strip().upper() == 'TRUE':
                    st.success("✅ Operação Aprovada")
                else:
                    st.error("❌ Operação Reprovada")
                
                st.markdown("---")
                # CORREÇÃO CRÍTICA: Altere estes nomes de coluna para corresponder à sua planilha 'info_guindauto'.
                st.write(f"**Operador:** {dados_guindauto.get('Nome do Operador', 'N/A')}")
                st.write(f"**Veículo (Placa):** {dados_guindauto.get('Placa do Veículo', 'N/A')}")

            st.markdown("---")
            render_document_status(dados_guindauto)
            
            with st.expander("Ver todos os dados brutos desta avaliação"):
                st.subheader("Dados de Içamento")
                st.dataframe(result_lifting.T, use_container_width=True)
                st.subheader("Informações do Guindauto")
                result_crane_clickable = make_urls_clickable(result_crane.copy())
                st.markdown(result_crane_clickable.T.to_html(escape=False), unsafe_allow_html=True)

        else:
            st.warning(f"Nenhum registro completo encontrado para o ID: {search_id}. Verifique se o ID está correto e se há dados em ambas as planilhas.")

    st.markdown("---")
    st.subheader("Histórico Completo (Visão Geral)")
    
    tab1, tab2 = st.tabs(["Dados de Içamento", "Informações do Guindauto"])

    with tab1:
        if not df_lifting.empty:
            st.dataframe(df_lifting, use_container_width=True)
        else:
            st.info("Nenhum histórico de dados de içamento encontrado.")

    with tab2:
        if not df_crane.empty:
            df_crane_clickable = make_urls_clickable(df_crane.copy())
            st.markdown(df_crane_clickable.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Nenhum histórico de informações de guindauto encontrado.")


