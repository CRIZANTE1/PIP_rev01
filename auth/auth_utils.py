# FILE: auth/auth_utils.py

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
    """Retorna o nome de exibição do usuário"""
    try:
        if hasattr(st.user, 'name'):
            return st.user.name
        elif hasattr(st.user, 'email'):
            return st.user.email
        return "Usuário"
    except Exception:
        return "Usuário"

@st.cache_data(ttl=600) # Cache para não verificar a planilha a cada interação
def get_admin_users_by_name():
    """
    Busca a lista de NOMES de administradores da planilha Google.
    Retorna uma lista de nomes.
    """
    try:
        uploader = GoogleDriveUploader()
        admin_data = uploader.get_data_from_sheet(ADMIN_SHEET_NAME)
        if not admin_data or len(admin_data) < 2:
            st.warning("Aba de administradores não encontrada ou vazia na planilha.")
            return []
        
        df = pd.DataFrame(admin_data[1:], columns=admin_data[0])
        if 'Nome' in df.columns:
            return [str(name).strip() for name in df['Nome'].dropna() if name]
        else:
            st.error("A aba 'Admins' precisa de uma coluna chamada 'Nome'.")
            return []
    except Exception as e:
        st.error(f"Erro ao buscar lista de administradores: {e}")
        return []

def is_admin_user():
    """
    Verifica se o NOME do usuário logado atualmente está na lista de administradores.
    """
    user_name = get_user_display_name()
    if not user_name or user_name == "Usuário":
        return False
    
    admin_list = get_admin_users_by_name()
    # Compara o nome do usuário com a lista de nomes de administradores
    return user_name.strip() in admin_list



