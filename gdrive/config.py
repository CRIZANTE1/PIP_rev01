import os
import json
import streamlit as st



try:
    # ID da pasta no Google Drive onde os arquivos serão salvos
    GDRIVE_FOLDER_ID = st.secrets.gdrive_config.folder_id

    # ID da planilha compartilhada para dados de içamento e guindauto
    GDRIVE_SHEETS_ID = st.secrets.gdrive_config.sheets_id

    # Nome das abas na planilha
    LIFTING_SHEET_NAME = st.secrets.gdrive_config.lifting_sheet_name
    CRANE_SHEET_NAME = st.secrets.gdrive_config.crane_sheet_name
    ADMIN_SHEET_NAME = st.secrets.gdrive_config.admin_sheet_name
    RAG_SHEET_NAME = "st.secrets.rag_config.sheet_name"
    
except (AttributeError, KeyError):
    st.error(
        "Erro de configuração: As chaves do Google Drive não foram encontradas nos secrets. "
        "Por favor, certifique-se de que a seção `[gdrive_config]` está corretamente configurada "
        "em seu arquivo .streamlit/secrets.toml."
    )
    # Define valores padrão para evitar que o app quebre completamente na inicialização
    GDRIVE_FOLDER_ID = ""
    GDRIVE_SHEETS_ID = ""
    LIFTING_SHEET_NAME = ""
    CRANE_SHEET_NAME = ""
    ADMIN_SHEET_NAME = ""
    RAG_SHEET_NAME = ""

def get_credentials_dict():
    """Retorna as credenciais do serviço do Google, seja do arquivo local ou do Streamlit Cloud."""
    if st.runtime.exists():
        # Se estiver rodando no Streamlit Cloud ou com secrets configurados
        try:
            return {
                "type": st.secrets.connections.gsheets.type,
                "project_id": st.secrets.connections.gsheets.project_id,
                "private_key_id": st.secrets.connections.gsheets.private_key_id,
                "private_key": st.secrets.connections.gsheets.private_key,
                "client_email": st.secrets.connections.gsheets.client_email,
                "client_id": st.secrets.connections.gsheets.client_id,
                "auth_uri": st.secrets.connections.gsheets.auth_uri,
                "token_uri": st.secrets.connections.gsheets.token_uri,
                "auth_provider_x509_cert_url": st.secrets.connections.gsheets.auth_provider_x509_cert_url,
                "client_x509_cert_url": st.secrets.connections.gsheets.client_x509_cert_url,
                "universe_domain": st.secrets.connections.gsheets.universe_domain
            }
        except Exception as e:
            st.error("Erro ao carregar credenciais do Google do Streamlit Secrets. Certifique-se de que as credenciais estão configuradas corretamente em [connections.gsheets].")
            raise e
    else:
        # Se estiver rodando localmente
        credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar credenciais do arquivo local: {str(e)}")
            raise e


