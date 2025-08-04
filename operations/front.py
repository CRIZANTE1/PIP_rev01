import streamlit as st
import uuid
from datetime import datetime
import logging

from gdrive.gdrive_upload import GoogleDriveUploader
from AI.api_Operation import PDFQA
from operations.ui_sections import (
    render_calculation_tab,
    render_operator_section,
    render_equipment_section,
    render_documentation_section,
    render_save_buttons
)

logging.basicConfig(level=logging.INFO)

# --------------------- Funções Utilitárias (Locais) --------------------

def mostrar_instrucoes():
    with st.expander("📖 Como usar este aplicativo", expanded=False):
        st.markdown("""### Guia de Uso
        
        1. **Aba "Dados do Içamento"**:
           * Preencha os dados da carga e do guindaste e clique em **Calcular**.
        
        2. **Aba "Informações e Documentos"**:
            - **Extração com IA**: Faça o upload dos documentos (CNH, CRLV, etc.) e clique nos botões "Extrair Dados" para preencher automaticamente os campos.
            - **Preenchimento Manual**: Preencha ou corrija os demais campos necessários.
            - **Documentos**: Faça o upload de todos os outros documentos solicitados.
        
        3. **Salvar**: Após conferir tudo, clique em **"💾 Salvar Todas as Informações"** para registrar a operação completa.
        """)

def gerar_id_avaliacao():
    return f"AV{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

def initialize_session_state():
    """Inicializa as chaves necessárias no session_state para o formulário."""
    form_keys = [
        'empresa_form', 'cnpj_form', 'telefone_form', 'email_form', 
        'operador_form', 'cpf_form', 'cnh_form', 'cnh_validade_form', 'cnh_status', 
        'placa_form', 'modelo_form', 'fabricante_form', 'ano_form', 
        'art_num_form', 'art_validade_form', 'art_status', 'obs_form', 
        'nr11_modulo_form', 'nr11_validade_form', 'nr11_status',
        'mprev_data_form', 'mprev_prox_form', 'mprev_status'
    ]
    for key in form_keys:
        if key not in st.session_state: st.session_state[key] = ""
    
    if 'id_avaliacao' not in st.session_state: st.session_state.id_avaliacao = gerar_id_avaliacao()
    if 'dados_icamento' not in st.session_state: st.session_state.dados_icamento = {}

# --------------------- PÁGINA PRINCIPAL (ORQUESTRADOR) --------------------
def front_page():
    initialize_session_state()
    st.title("Calculadora de Movimentação de Carga")
    mostrar_instrucoes()
    
    tab1, tab2 = st.tabs(["📝 Dados do Içamento", "🏗️ Informações e Documentos"])

    # --- ABA 1: CÁLCULO DE IÇAMENTO ---
    with tab1:
        render_calculation_tab()

    # --- ABA 2: INFORMAÇÕES E DOCUMENTOS ---
    with tab2:
        st.header("Informações e Documentos do Guindauto")
        st.info(f"ID da Avaliação: **{st.session_state.id_avaliacao}**")
        
        # Instanciar helpers uma única vez
        uploader = GoogleDriveUploader()
        ai_processor = PDFQA()
        
        # Seção de Empresa
        st.subheader("📋 Dados da Empresa")
        col_c1, col_c2 = st.columns(2)
        with col_c1: st.text_input("Empresa", key="empresa_form"); st.text_input("CNPJ", key="cnpj_form")
        with col_c2: st.text_input("Telefone", key="telefone_form"); st.text_input("Email", key="email_form")

        # Renderizar seções e coletar os arquivos de upload
        cnh_file = render_operator_section(ai_processor)
        crlv_file = render_equipment_section(ai_processor)
        art_file, nr11_file, mprev_file = render_documentation_section(ai_processor)
        
        st.subheader("Upload de Gráfico de Carga")
        grafico_carga_file = st.file_uploader("Gráfico de Carga (.pdf, .png)", key="grafico_uploader", label_visibility="collapsed")
        st.text_area("Observações Adicionais", key="obs_form")
        
        st.divider()

        # Agrupar arquivos para passar para a função de salvamento
        files_to_upload = {
            'cnh_doc': cnh_file, 'crlv_doc': crlv_file, 'art_doc': art_file, 
            'nr11_doc': nr11_file, 'mprev_doc': mprev_file, 'grafico_doc': grafico_carga_file
        }
        
        render_save_buttons(uploader, files_to_upload)

