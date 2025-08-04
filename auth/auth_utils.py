import streamlit as st
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import ADMIN_SHEET_NAME
import pandas as pd

def is_oidc_available():
    """Verifica se o login OIDC está configurado e disponível"""
    try:
        return hasattr(st.user, 'is_logged_in')
    except Exception:
        return False

def is_user_logged_in():
    """Verifica se o usuário está logado"""
    try:
        return st.user.is_logged_in
    except Exception:
        return False

def get_user_display_name():
    """Retorna o nome de exibição do usuário (usado para saudação)"""
    try:
        if hasattr(st.user, 'name') and st.user.name:
            return st.user.name
        elif hasattr(st.user, 'email') and st.user.email:
            return st.user.email
        return "Usuário"
    except Exception:
        return "Usuário"

def get_user_email():
    """Retorna o email do usuário logado, que é o identificador único."""
    try:
        if hasattr(st.user, 'email') and st.user.email:
            return st.user.email
        return None
    except Exception:
        return None

@st.cache_data(ttl=600) # Cache para não verificar a planilha a cada interação
def get_admin_users_by_email():
    """
    Busca a lista de E-MAILS de administradores da planilha Google.
    Retorna uma lista de e-mails em minúsculas.
    """
    try:
        uploader = GoogleDriveUploader()
        admin_data = uploader.get_data_from_sheet(ADMIN_SHEET_NAME)
        if not admin_data or len(admin_data) < 2:
            st.warning("Aba de administradores ('adm') não encontrada ou vazia na planilha.")
            return []
        
        df = pd.DataFrame(admin_data[1:], columns=admin_data[0])
        # Procura pela coluna 'Email' (case-insensitive)
        email_col = next((col for col in df.columns if col.strip().lower() == 'email'), None)

        if email_col:
            # Retorna a lista de emails, normalizados (sem espaços e em minúsculas)
            return [str(email).strip().lower() for email in df[email_col].dropna() if email]
        else:
            st.error("A aba 'adm' da sua planilha precisa de uma coluna chamada 'Email'.")
            return []
    except Exception as e:
        st.error(f"Erro ao buscar lista de administradores por e-mail: {e}")
        return []

def is_admin_user():
    """
    Verifica se o E-MAIL do usuário logado atualmente está na lista de administradores.
    A verificação é case-insensitive.
    """
    user_email = get_user_email()
    if not user_email:
        return False
    
    admin_list = get_admin_users_by_email()
    
    # Compara o email do usuário (normalizado) com a lista de emails de administradores
    return user_email.strip().lower() in admin_list


