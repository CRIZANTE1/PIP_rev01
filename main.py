import streamlit as st

from auth.login_page import show_login_page, show_user_header, show_logout_button
from auth.auth_utils import is_user_logged_in, get_user_role, is_session_expired
from app.utils import get_sao_paulo_time
from app.data_operations import load_data_from_sheets
from app.logger import log_action
from app.ui_interface import vehicle_access_interface
from app.admin_page import admin_page
from app.summary_page import summary_page 
from app.scheduling_page import scheduling_page
from app.security import SessionSecurity

st.set_page_config(page_title="Controle de Acesso BAERI", layout="wide")

def limpar_estados_conflitantes():
    """Remove estados de widgets que podem causar conflitos"""
    # Lista de keys de widgets que podem causar conflitos
    conflicting_keys = [
        'angulo_minimo_input',
        'person_selector',
        'fora_placa',
        'fora_empresa',
        'fora_select',
        'fora_ciente',
        'novo_nome',
        'novo_cpf',
        'novo_empresa',
        'novo_placa',
        'novo_marca',
        'novo_select',
        'novo_ciente',
        'block_person',
        'delete_person',
    ]
    
    # Remove apenas se existir no session_state
    for key in conflicting_keys:
        if key in st.session_state:
            # Não remove se for um estado importante como 'processing'
            if key not in ['processing', 'df_acesso_veiculos', 'login_time', 'login_logged', 'last_activity']:
                try:
                    del st.session_state[key]
                except:
                    pass

def main():
    # Inicializa segurança de sessão
    SessionSecurity.init_session_security()
    
    # Carrega os dados se ainda não estiverem na sessão
    if 'df_acesso_veiculos' not in st.session_state:
        load_data_from_sheets()

    if is_user_logged_in():
        
        # Verifica timeout de sessão por inatividade
        is_expired, minutes = SessionSecurity.check_session_timeout(timeout_minutes=30)
        if is_expired:
            st.warning(f"⚠️ Sua sessão expirou após {int(minutes)} minutos de inatividade. Por favor, faça login novamente.")
            log_action("SESSION_TIMEOUT", f"Sessão expirou por inatividade ({int(minutes)} minutos)")
            
            # Limpa estados conflitantes antes de fazer logout
            limpar_estados_conflitantes()
            
            keys_to_clear = ['login_time', 'login_logged', 'last_activity']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.logout()
            st.rerun()
        
        if 'login_time' not in st.session_state:
            st.session_state.login_time = get_sao_paulo_time()

        if is_session_expired():
            st.warning("Sua sessão expirou devido à troca de turno. Por favor, faça login novamente.")
            log_action("SESSION_EXPIRED", "Sessão do usuário expirou automaticamente.")
            
            # Limpa estados conflitantes antes de fazer logout
            limpar_estados_conflitantes()
            
            keys_to_clear = ['login_time', 'login_logged']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.logout()
            st.rerun()

        user_role = get_user_role()

        if user_role is None:
            st.error("Acesso Negado. Seu usuário não tem permissão para usar este sistema.")
            st.warning("Por favor, entre em contato com o administrador para solicitar seu cadastro.")
            st.stop() 

        if 'login_logged' not in st.session_state:
            log_action("LOGIN", f"Usuário acessou o sistema com papel '{user_role}'.")
            st.session_state.login_logged = True
            
        
        show_user_header()
        show_logout_button()
        
        page_options = []
        if user_role == 'admin':
            page_options.extend(["Controle de Acesso", "Agendar Visita", "Painel Administrativo", "Resumo"])
        elif user_role == 'operacional':
            page_options.extend(["Controle de Acesso", "Resumo"])
        
        page = st.sidebar.selectbox("Escolha a página:", page_options)
        
        # Limpa estados conflitantes ao trocar de página
        if 'current_page' not in st.session_state:
            st.session_state.current_page = page
        elif st.session_state.current_page != page:
            limpar_estados_conflitantes()
            st.session_state.current_page = page
        
        if page == "Controle de Acesso":
            vehicle_access_interface()
        elif page == "Agendar Visita":
            scheduling_page()    
        elif page == "Painel Administrativo" and user_role == 'admin':
            admin_page()
        elif page == "Resumo": 
            summary_page()
    else:
        # Garante que, se o usuário não estiver logado, o estado da sessão seja limpo
        limpar_estados_conflitantes()
        
        keys_to_clear = ['login_time', 'login_logged']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
            
        show_login_page()

    
    st.caption('Desenvolvido por Cristian Ferreira Carlos, CE9X,+551131038708, cristiancarlos@vibraenergia.com.br')
    

if __name__ == "__main__":
    main()



