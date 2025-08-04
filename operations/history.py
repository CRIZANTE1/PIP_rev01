import streamlit as st
import pandas as pd
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from operations.plot import criar_diagrama_guindaste 

@st.cache_data(ttl=600)
def load_sheet_data(sheet_name):
    """
    Carrega dados de uma aba específica do Google Sheets e os converte em um DataFrame.
    """
    try:
        uploader = GoogleDriveUploader()
        data = uploader.get_data_from_sheet(sheet_name)
        
        if not data or len(data) < 2:
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
        # CORREÇÃO: Usando .str.contains para ser mais flexível com os nomes das colunas de URL
        if isinstance(df[col].dtype, object) and df[col].str.contains('http', na=False).any():
            df[col] = df[col].apply(lambda x: f'<a href="{x}" target="_blank">Abrir Link</a>' if pd.notna(x) and str(x).startswith('http') else "N/A")
    return df

def render_document_status(dados_guindauto):
    """
    Renderiza uma lista de documentos com ícones de status (✅/❌) e links.
    """
    st.subheader("Documentos Avaliados")

    # Ponto de Atenção: Os nomes das colunas aqui (ex: 'URL_ART') DEVEM corresponder
    # exatamente aos cabeçalhos na sua planilha de "Informações do Guindauto".
    doc_map = {
        "ART (Anot. Resp. Técnica)": "URL_ART",
        "Certificado NR-11": "URL_NR11",
        "CNH do Operador": "URL_CNH",
        "CRLV do Veículo": "URL_CRLV",
        "Manutenção Preventiva": "URL_M_PREV",
        "Gráfico de Carga": "URL_GRAFICO"
    }

    for doc_name, col_name in doc_map.items():
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
    # Converte para string, substitui vírgula por ponto, e então converte para numérico
    return pd.to_numeric(str(series).replace(',', '.'), errors='coerce')

def render_diagrama(dados_icamento):
    """
    Renderiza o diagrama de içamento a partir dos dados históricos.
    """
    st.subheader("Diagrama da Operação")
    
    try:
        # CORREÇÃO: Usando os nomes de coluna corretos do seu arquivo e a conversão segura.
        raio_max = safe_to_numeric(dados_icamento.get('Raio Máximo (m)'))
        alcance_max = safe_to_numeric(dados_icamento.get('Alcance Máximo (m)'))
        carga_total = safe_to_numeric(dados_icamento.get('Carga Total (kg)'))
        capacidade_raio = safe_to_numeric(dados_icamento.get('Capacidade Raio (kg)'))
        angulo_minimo = safe_to_numeric(dados_icamento.get('Ângulo Mínimo da Lança'))
        
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

    if df_lifting.empty and df_crane.empty:
        st.warning("Não foi possível carregar os dados do histórico ou as planilhas estão vazias.")
        return

    st.subheader("Buscar e Analisar Avaliação por ID")
    id_column = df_lifting.columns[0] if not df_lifting.empty else (df_crane.columns[0] if not df_crane.empty else None)
    
    if id_column:
        search_id = st.text_input("Digite o ID da Avaliação (ex: AV20240101-abcdefgh)", key="search_id_input")

        if st.button("Buscar por ID", key="search_button") and search_id:
            st.markdown("---")
            
            result_lifting = df_lifting[df_lifting[id_column] == search_id]
            result_crane = df_crane[df_crane[id_column] == search_id]

            if not result_lifting.empty and not result_crane.empty:
                dados_icamento = result_lifting.iloc[0]
                dados_guindauto = result_crane.iloc[0]

                st.header(f"Análise Detalhada da Avaliação: {search_id}")

                col1, col2 = st.columns([2, 1])

                with col1:
                    render_diagrama(dados_icamento)

                with col2:
                    st.subheader("Principais Indicadores")
                    
                    # CORREÇÃO: Usando o nome correto da coluna e a função de conversão segura.
                    carga_total_val = safe_to_numeric(dados_icamento.get('Carga Total (kg)', 0))
                    st.metric("Carga Total da Operação", f"{carga_total_val:,.2f} kg".replace(",", "."))
                    
                    # CORREÇÃO: Usando os nomes corretos das colunas de utilização.
                    st.metric("Utilização no Raio", dados_icamento.get('% Utilização Raio', 'N/A'))
                    st.metric("Utilização na Lança", dados_icamento.get('% Utilização Alcance', 'N/A'))
                    
                    # CORREÇÃO: Usando o nome correto da coluna 'Adequado'.
                    adequado = dados_icamento.get('Adequado')
                    if str(adequado).strip().upper() == 'TRUE':
                        st.success("✅ Operação Aprovada")
                    else:
                        st.error("❌ Operação Reprovada")
                    
                    st.markdown("---")
                    # CORREÇÃO: Os nomes das colunas de operador e placa precisam ser exatos.
                    # Verifique sua planilha, estes são palpites comuns.
                    st.write(f"**Operador:** {dados_guindauto.get('Nome do Operador', 'N/A')}")
                    st.write(f"**Veículo (Placa):** {dados_guindauto.get('Placa', 'N/A')}")

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

