import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from operations.front import front_page
from operations.history import show_history_page
from operations.demo_page import show_demo_page
from auth.login_page import show_login_page, show_user_header, show_logout_button
from auth.auth_utils import is_user_logged_in, is_admin_user

def main():
    st.set_page_config(
        page_title="Calculadora de Carga",
        page_icon="🏗️",
        layout="wide"
    )

    if not show_login_page():
        return

    show_user_header()
    show_logout_button()

    if is_admin_user():
        st.sidebar.success("✅ Acesso completo")
        tab_calc, tab_history = st.tabs(["Calculadora de Carga", "Histórico"])
        with tab_calc:
            front_page()
        with tab_history:
            show_history_page()
    else:
        st.sidebar.error("🔒 Acesso de demonstração")
        show_demo_page()

if __name__ == "__main__":
    main()
    st.caption('Copyright 2024, Cristian Ferreira Carlos, Todos os direitos reservados.')
    st.caption('https://www.linkedin.com/in/cristian-ferreira-carlos-256b19161/')
