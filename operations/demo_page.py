import streamlit as st

def show_demo_page():
    """
    Exibe uma página de demonstração para usuários não autorizados.
    """
    st.title("Calculadora de Movimentação de Carga")

    # URL do vídeo de demonstração
    video_url = 'https://youtu.be/N9uRR15_uNg'
    st.video(video_url)

    st.header("Versão de Demonstração")
    st.warning("🔒 Acesso restrito. Esta é uma versão de demonstração apenas para visualização.")
    
    st.markdown("""
    Você está vendo esta página porque seu usuário não tem permissão para acessar a versão completa da aplicação.

    ### Funcionalidades da Versão Completa:
    - **Cálculos Detalhados**: Cálculo de carga total com margens de segurança.
    - **Validação de Equipamento**: Análise de capacidade do guindaste com base em raio e alcance.
    - **Extração com IA**: Leitura automática de dados de documentos como CNH, CRLV e ART.
    - **Registro Completo**: Salvamento de todas as operações, incluindo documentos, no Google Drive e Google Sheets.
    - **Histórico de Operações**: Consulta a todos os registros salvos.

    ---
    
    **Para obter acesso, por favor, entre em contato com o administrador do sistema.**
    """)
    
    try:
        user_name = st.user.name
        st.info(f"Seu nome de login é: **{user_name}**. Se você deveria ter acesso, forneça este nome ao administrador.")
    except Exception:
        st.info("Para obter acesso, por favor, entre em contato com o administrador do sistema.")
