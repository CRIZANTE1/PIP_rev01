
import streamlit as st
import pandas as pd
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME


@st.cache_data(ttl=600)
def load_sheet_data(sheet_name):
    """
    Carrega dados de uma aba específica do Google Sheets e os converte em um DataFrame do Pandas.
    A função é armazenada em cache para melhor desempenho.
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
    """Transforma colunas que contêm URLs em links HTML clicáveis."""
    for col in df.columns:
        if "URL" in col.upper():
            df[col] = df[col].apply(lambda x: f'<a href="{x}" target="_blank">Abrir Link</a>' if pd.notna(x) and str(x).startswith('http') else "N/A")
    return df

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

    st.subheader("Buscar Avaliação por ID")
    # Usa a primeira coluna (geralmente 'ID') para a busca
    id_column = df_lifting.columns[0] if not df_lifting.empty else (df_crane.columns[0] if not df_crane.empty else None)
    
    if id_column:
        search_id = st.text_input("Digite o ID da Avaliação (ex: AV20240101-abcdefgh)", key="search_id_input")

        if st.button("Buscar por ID", key="search_button"):
            if search_id:
                st.markdown("---")
                st.subheader(f"Resultados para o ID: {search_id}")

                # Busca no DataFrame de Içamento
                result_lifting = df_lifting[df_lifting[id_column] == search_id]
                if not result_lifting.empty:
                    with st.expander("Dados de Içamento", expanded=True):
                        # Transpõe o DataFrame para melhor visualização de um único registro
                        st.dataframe(result_lifting.T, use_container_width=True)
                else:
                    st.info("Nenhum dado de içamento encontrado para este ID.")
                
                # Busca no DataFrame de Guindauto
                result_crane = df_crane[df_crane[id_column] == search_id]
                if not result_crane.empty:
                    with st.expander("Informações do Guindauto", expanded=True):
                        # Formata as URLs para serem clicáveis antes de exibir
                        result_crane_clickable = make_urls_clickable(result_crane.copy())
                        # Transpõe e exibe como HTML para renderizar os links
                        st.markdown(result_crane_clickable.T.to_html(escape=False), unsafe_allow_html=True)
                else:
                    st.info("Nenhuma informação de guindauto encontrada para este ID.")

            else:
                st.warning("Por favor, digite um ID para buscar.")

    st.markdown("---")
    st.subheader("Histórico Completo")
    
    tab1, tab2 = st.tabs(["Dados de Içamento", "Informações do Guindauto"])

    with tab1:
        if not df_lifting.empty:
            st.dataframe(df_lifting, use_container_width=True)
        else:
            st.info("Nenhum histórico de dados de içamento encontrado.")

    with tab2:
        if not df_crane.empty:
            df_crane_clickable = make_urls_clickable(df_crane.copy())
            # Exibe o DataFrame como HTML para que os links funcionem
            st.markdown(df_crane_clickable.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("Nenhum histórico de informações de guindauto encontrado.")
