import streamlit as st
import sys
import os
from operations.front import front_page
from operations.history import show_history_page # Importa a nova página de histórico
from auth.login_page import show_login_page, show_user_header, show_logout_button

def configurar_pagina():
    st.set_page_config(
        page_title="Calculadora de Movimentação de Carga",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            'Get Help': 'https://www.streamlit.io/community',
            'Report a bug': "mailto:cristianfc2015@hotmail.com",
            'About': """
            ## Calculadora de Carga para Guindauto
            
            Esta aplicação calcula e valida cargas para operações de içamento de carga com guindaste e guindauto, 
            o plano rigging não deve ser descartado.
            
            * Calcula margens de segurança
            * Valida capacidades do guindaste
            * Considera pesos de acessórios e cabos
            
            Versão 1.0.0
            """
        }
    )

def main():
    configurar_pagina()
    if show_login_page():
        st.session_state.user = st.session_state.user if 'user' in st.session_state else None
        show_user_header()
        show_logout_button()
        front_page()
    
        # Adiciona navegação por abas para as diferentes páginas
        tab_calc, tab_history = st.tabs(["Calculadora de Carga", "Histórico de Avaliações"])

        with tab_calc:
            front_page()
        
        with tab_history:
            show_history_page()

if __name__ == "__main__":
    main()
    st.caption ('Copyright 2024, Cristian Ferreira Carlos, Todos os direitos reservados.' )
    st.caption ('https://www.linkedin.com/in/cristian-ferreira-carlos-256b19161/')

