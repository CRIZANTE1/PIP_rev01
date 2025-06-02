import os
import json
import streamlit as st

# ID da pasta no Google Drive onde os arquivos serão salvos
GDRIVE_FOLDER_ID = "1eCuybshDxOjOmJ7aYDnClatc4Ow_4zRL"

# ID da planilha compartilhada para dados de içamento e guindauto
GDRIVE_SHEETS_ID = "1nH_iF223sNXqbfItbvLZrnIadgJf7Q00M4prjFgGq7c"


# Nome das abas na planilha
LIFTING_SHEET_NAME = "Dados_Icamento"
CRANE_SHEET_NAME = "Info_Guindauto"

def get_credentials_dict():
    """Retorna as credenciais do serviço do Google, seja do arquivo local ou do Streamlit Cloud."""
    if st.runtime.exists():
        # Se estiver rodando no Streamlit Cloud ou com secrets configurados
        try:
            return json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        except Exception as e:
            st.error("Erro ao carregar credenciais do Google do Streamlit Secrets. Certifique-se de que GOOGLE_SERVICE_ACCOUNT está configurado corretamente.")
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