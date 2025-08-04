import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st
from gdrive.config import get_credentials_dict, GDRIVE_FOLDER_ID, GDRIVE_SHEETS_ID
import tempfile
import gspread

class GoogleDriveUploader:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self.credentials = None
        self.drive_service = None
        self.sheets_service = None 
        self.initialize_services()

    def initialize_services(self):
        """Inicializa os serviços do Google Drive e Google Sheets (usando gspread)"""
        try:
            credentials_dict = get_credentials_dict()
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=self.SCOPES
            )
            # O serviço do Drive continua o mesmo
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            
            # MUDANÇA: Inicializa o gspread em vez da API do Sheets
            self.sheets_service = gspread.authorize(self.credentials)
            
        except Exception as e:
            st.error(f"Erro ao inicializar serviços do Google: {str(e)}")
            raise

    def upload_file(self, arquivo, novo_nome=None):
        """
        Faz upload do arquivo para o Google Drive.
        ESTA FUNÇÃO NÃO PRECISA DE MUDANÇAS.
        """
        st.info("Iniciando processo de upload do arquivo.")
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.name)[1])
            temp_file.write(arquivo.getbuffer())
            temp_file.close()
            temp_path = temp_file.name
            
            file_metadata = {
                'name': novo_nome if novo_nome else arquivo.name,
                'parents': [GDRIVE_FOLDER_ID]
            }
            media = MediaFileUpload(temp_path, mimetype=arquivo.type, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            return file.get('webViewLink')
        except Exception as e:
            if "HttpError 404" in str(e) and GDRIVE_FOLDER_ID in str(e):
                st.error(f"Erro: A pasta do Google Drive com ID '{GDRIVE_FOLDER_ID}' não foi encontrada. Verifique as permissões.")
            else:
                st.error(f"Erro ao fazer upload do arquivo: {str(e)}")
            raise
        finally:
            if temp_file and os.path.exists(temp_path):
                os.remove(temp_path)

    def append_data_to_sheet(self, sheet_name, data_row):
        """
        MUDANÇA: Adiciona uma nova linha de dados à planilha usando gspread.
        """
        try:
            # Abre a planilha pelo ID e seleciona a aba pelo nome
            spreadsheet = self.sheets_service.open_by_key(GDRIVE_SHEETS_ID)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Adiciona a linha no final da aba
            # 'RAW' garante que os dados sejam inseridos como o usuário digitou
            result = worksheet.append_row(data_row, value_input_option='RAW')
            return result
            
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Erro: A aba com o nome '{sheet_name}' não foi encontrada na sua planilha. Verifique o nome no arquivo secrets.toml.")
            raise
        except Exception as e:
            st.error(f"Erro ao adicionar dados à planilha '{sheet_name}' com gspread: {str(e)}")
            raise

    def get_data_from_sheet(self, sheet_name):
        """
        MUDANÇA: Lê todos os dados de uma aba específica usando gspread.
        """
        try:
            # Abre a planilha pelo ID e seleciona a aba pelo nome
            spreadsheet = self.sheets_service.open_by_key(GDRIVE_SHEETS_ID)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Pega todos os valores da planilha
            values = worksheet.get_all_values()
            return values
            
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Erro: A aba com o nome '{sheet_name}' não foi encontrada na sua planilha. Verifique o nome no arquivo secrets.toml.")
            return None # Retorna None para indicar o erro
        except Exception as e:
            st.error(f"Erro ao ler dados da planilha '{sheet_name}' com gspread: {str(e)}")
            raise
