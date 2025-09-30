import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, date
import time
import logging

from operations.plot import criar_diagrama_guindaste
from operations.calc import calcular_carga_total, validar_guindaste
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from AI.api_Operation import PDFQA
from utils.prompts import get_crlv_prompt, get_art_prompt, get_cnh_prompt, get_nr11_prompt, get_mprev_prompt

logging.basicConfig(level=logging.INFO)

def mostrar_instrucoes():
    with st.expander("📖 Como usar este aplicativo", expanded=False):
        st.markdown("""
        #### Guia Rápido de Uso
        
        Siga estes passos para realizar uma análise de içamento completa:
        
        ---
        
        ##### **Aba 1: 📝 Dados do Içamento**
        
        1.  **Dados da Carga:**
            -   **Peso da Carga (kg):** Informe o peso principal a ser içado.
            -   **Peso dos Acessórios (kg):** Adicione o peso de cintas, manilhas, etc.
        
        2.  **Estado do Equipamento:**
            -   Selecione **"Novo"** para aplicar uma margem de segurança de **10%**.
            -   Selecione **"Usado"** para aplicar uma margem de segurança de **25%**.
        
        3.  **Dados e Capacidades do Guindaste:**
            -   Preencha as informações do fabricante e modelo.
            -   Informe o **Raio Máximo** e a capacidade de carga nesse ponto.
            -   Informe a **Extensão Máxima da Lança** e a capacidade nesse ponto.
            -   Insira o **Ângulo Mínimo da Lança** conforme especificado pelo fabricante.

        4.  **Calcular:**
            -   Clique no botão **"Calcular"** para ver os resultados, a validação de segurança e o diagrama da operação.
        
        > ⚠️ **Atenção:** Se a utilização da capacidade do guindaste exceder **80%**, a operação é considerada de risco e requer análise adicional da engenharia.
        
        ---
        
        ##### **Aba 2: 🏗️ Informações e Documentos**
        
        1.  **Extração de Dados com IA:**
            -   **Operador:** Faça o upload do arquivo da **CNH** e clique em **"Extrair e Validar CNH com IA"**.
            -   **Equipamento:** Faça o upload do **CRLV** e clique em **"Extrair Dados do CRLV"**.
            -   Faça o mesmo para os documentos **ART**, **NR-11** e **Manutenção Preventiva**.
        
        2.  **Preenchimento Manual:**
            -   Complete ou corrija qualquer informação que não tenha sido preenchida automaticamente.
            -   Faça o upload do **Gráfico de Carga** do equipamento.
        
        3.  **Salvar Operação:**
            -   Após preencher todos os campos e verificar os documentos, clique em **"💾 Salvar Todas as Informações"**.
            -   Isso registrará a operação permanentemente no sistema.
        """)


def gerar_id_avaliacao():
    return f"AV{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

def handle_upload_with_id(uploader, arquivo, tipo_doc, id_avaliacao):
    if arquivo is None: 
        return None
    
    # Validação de tipo de arquivo
    extensao = arquivo.name.split('.')[-1].lower()
    tipos_permitidos = ['pdf', 'png', 'jpg', 'jpeg']
    
    if extensao not in tipos_permitidos:
        st.error(f"Tipo de arquivo não permitido: .{extensao}. Use: {', '.join(tipos_permitidos)}")
        return {'success': False, 'error': f'Tipo não permitido: .{extensao}'}
    
    # Validação de tamanho (10MB máximo)
    if hasattr(arquivo, 'size') and arquivo.size > 10 * 1024 * 1024:
        st.error(f"Arquivo muito grande ({arquivo.size / 1024 / 1024:.1f}MB). Máximo: 10MB")
        return {'success': False, 'error': 'Arquivo muito grande'}
    
    novo_nome = f"{id_avaliacao}_{tipo_doc}.{extensao}"
    try:
        file_url = uploader.upload_file(arquivo, novo_nome)
        return {'success': True, 'url': file_url, 'nome': novo_nome}
    except Exception as e:
        st.error(f"Erro no upload de '{novo_nome}': {e}")
        logging.exception(f"Erro no upload de {novo_nome}")
        return {'success': False, 'error': str(e)}

def display_status(status_text):
    if not status_text: 
        return
    status_lower = status_text.lower()
    if "válido" in status_lower or "em dia" in status_lower:
        st.success(f"Status: {status_text}")
    elif "vencido" in status_lower:
        st.error(f"Status: {status_text}")
    else:
        st.warning(f"Status: {status_text}")

def inicializar_session_state():
    """Inicializa todos os campos do session_state com valores padrão"""
    # Campos de formulário
    form_keys = [
        'empresa_form', 'cnpj_form', 'telefone_form', 'email_form', 
        'operador_form', 'cpf_form', 'cnh_form', 'cnh_validade_form', 'cnh_status', 
        'placa_form', 'modelo_form', 'fabricante_form', 'ano_form', 
        'art_num_form', 'art_validade_form', 'art_status', 'obs_form', 
        'nr11_modulo_form', 'nr11_validade_form', 'nr11_status',
        'mprev_data_form', 'mprev_prox_form', 'mprev_status'
    ]
    for key in form_keys:
        if key not in st.session_state: 
            st.session_state[key] = ""
    
    # Estado do equipamento
    if 'estado_equip_radio' not in st.session_state:
        st.session_state.estado_equip_radio = "Novo"
    
    # Campos numéricos de cálculo
    numeric_defaults = {
        'peso_carga': 0.0,
        'peso_acessorios': 0.0,
        'raio_max': 0.0,
        'capacidade_raio': 0.0,
        'extensao_lanca': 0.0,
        'capacidade_alcance': 0.0,
        'angulo_minimo_input': 40.0
    }
    for key, default_value in numeric_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Strings de identificação do guindaste
    if 'fabricante_guindaste_calc' not in st.session_state:
        st.session_state.fabricante_guindaste_calc = ""
    if 'nome_guindaste_calc' not in st.session_state:
        st.session_state.nome_guindaste_calc = ""
    
    # ID e dados da avaliação
    if 'id_avaliacao' not in st.session_state: 
        st.session_state.id_avaliacao = gerar_id_avaliacao()
    if 'dados_icamento' not in st.session_state: 
        st.session_state.dados_icamento = {}

def validar_inputs_calculo():
    """Valida se todos os inputs necessários para o cálculo estão preenchidos corretamente"""
    try:
        # Verifica se todos os campos existem e têm valores válidos
        checks = {
            'peso_carga': st.session_state.get("peso_carga", 0) > 0,
            'raio_max': st.session_state.get("raio_max", 0) > 0,
            'capacidade_raio': st.session_state.get("capacidade_raio", 0) > 0,
            'extensao_lanca': st.session_state.get("extensao_lanca", 0) > 0,
            'capacidade_alcance': st.session_state.get("capacidade_alcance", 0) > 0,
            'estado_equipamento': st.session_state.get("estado_equip_radio") in ["Novo", "Usado"]
        }
        
        return all(checks.values()), checks
    except (KeyError, TypeError, AttributeError) as e:
        logging.error(f"Erro na validação de inputs: {e}")
        return False, {}

def front_page():
    # Inicialização do session_state
    inicializar_session_state()
    
    st.title("Calculadora de Movimentação de Carga")
    mostrar_instrucoes()
    
    tab1, tab2 = st.tabs(["📝 Dados do Içamento", "🏗️ Informações e Documentos"])

    # --- ABA 1: CÁLCULO DE IÇAMENTO ---
    with tab1:
        st.header("Análise e Simulação de Içamento")

        # --- Coluna de Inputs (à Esquerda) ---
        col_inputs, col_results = st.columns([1, 2], gap="large")
        with col_inputs:
            st.subheader("Parâmetros da Operação")
            
            st.radio(
                "Estado do Equipamento", 
                ["Novo", "Usado"], 
                key="estado_equip_radio", 
                help="Novo: 10% de margem. Usado: 25%."
            )
            
            # Alerta visual baseado no estado
            if st.session_state.estado_equip_radio == "Novo":
                st.info("Margem de segurança de 10% aplicada.")
            else:
                st.warning("⚠️ Margem de segurança de 25% aplicada para equipamento usado.")

            st.number_input(
                "Peso da carga (kg)", 
                min_value=0.0, 
                step=100.0, 
                key="peso_carga",
                help="Peso principal do item a ser içado"
            )
            st.number_input(
                "Peso dos acessórios (kg)", 
                min_value=0.0, 
                step=1.0, 
                key="peso_acessorios",
                help="Peso de cintas, manilhas, grilhetas, etc."
            )

            st.divider()
            
            st.text_input(
                "Fabricante do Guindaste", 
                key="fabricante_guindaste_calc",
                placeholder="Ex: Liebherr, Grove, Terex"
            )
            st.text_input(
                "Nome do Guindaste", 
                key="nome_guindaste_calc", 
                placeholder="Ex: AGI, XCA250 BR II"
            )
            
            st.number_input(
                "Raio de Operação (m)", 
                min_value=0.0, 
                step=0.1, 
                key="raio_max",
                help="Distância horizontal do centro do guindaste até o ponto de içamento"
            )
            st.number_input(
                "Capacidade no Raio (kg)", 
                min_value=0.0, 
                step=100.0, 
                key="capacidade_raio",
                help="Capacidade máxima do guindaste no raio informado"
            )
            
            st.number_input(
                "Extensão da Lança (m)", 
                min_value=0.0, 
                step=0.1, 
                key="extensao_lanca",
                help="Comprimento total da lança do guindaste"
            )
            st.number_input(
                "Capacidade na Lança (kg)", 
                min_value=0.0, 
                step=100.0, 
                key="capacidade_alcance",
                help="Capacidade máxima na extensão máxima da lança"
            )

            st.number_input(
                "Ângulo Mínimo da Lança (°)", 
                min_value=1.0, 
                max_value=89.0, 
                value=40.0,
                key="angulo_minimo_input",
                help="Ângulo mínimo de segurança especificado pelo fabricante"
            )

        # --- Coluna de Resultados (à Direita) ---
        with col_results:
            st.subheader("Resultados e Análise em Tempo Real")
            
            # Validação de inputs
            inputs_validos, checks = validar_inputs_calculo()

            if not inputs_validos:
                st.info("📊 Preencha todos os parâmetros à esquerda para ver os resultados e o diagrama.")
                
                # Mostrar quais campos estão faltando
                campos_faltantes = [campo for campo, valido in checks.items() if not valido]
                if campos_faltantes:
                    with st.expander("Campos pendentes"):
                        for campo in campos_faltantes:
                            st.write(f"• {campo.replace('_', ' ').title()}")
            else:
                try:
                    # Validação de geometria antes do cálculo
                    if st.session_state.extensao_lanca < st.session_state.raio_max:
                        st.error("⚠️ ERRO: A extensão da lança não pode ser menor que o raio de operação!")
                        st.warning(f"Extensão da lança: {st.session_state.extensao_lanca}m | Raio: {st.session_state.raio_max}m")
                    else:
                        # Cálculo da carga total
                        equip_novo = st.session_state.estado_equip_radio == "Novo"
                        resultado_calc = calcular_carga_total(
                            st.session_state.peso_carga, 
                            equip_novo, 
                            st.session_state.peso_acessorios
                        )
                        
                        # Validação do guindaste
                        validacao = validar_guindaste(
                            carga_total=resultado_calc['carga_total'], 
                            capacidade_raio=st.session_state.capacidade_raio, 
                            capacidade_alcance_max=st.session_state.capacidade_alcance, 
                            raio_max=st.session_state.raio_max, 
                            extensao_lanca=st.session_state.extensao_lanca,
                            angulo_minimo_fabricante=st.session_state.angulo_minimo_input
                        )

                        # Armazenar dados para uso posterior
                        st.session_state.dados_icamento = {
                            **resultado_calc,
                            'fabricante_guindaste': st.session_state.fabricante_guindaste_calc,
                            'nome_guindaste': st.session_state.nome_guindaste_calc,
                            'modelo_guindaste': "",
                            'raio_max': st.session_state.raio_max,
                            'capacidade_raio': st.session_state.capacidade_raio,
                            'extensao_lanca': st.session_state.extensao_lanca,
                            'capacidade_alcance': st.session_state.capacidade_alcance,
                            'angulo_minimo_fabricante': st.session_state.angulo_minimo_input,
                            'validacao': validacao
                        }

                        # Exibir mensagem de validação
                        mensagem_validacao = validacao.get('mensagem', 'Falha na validação.')
                        if "INSEGURA" in mensagem_validacao.upper():
                            st.error(f"❌ {mensagem_validacao}")
                        elif "ATENÇÃO" in mensagem_validacao.upper():
                            st.warning(f"⚠️ {mensagem_validacao}")
                        else:
                            st.success(f"✅ {mensagem_validacao}")
                        
                        # Diagrama
                        st.plotly_chart(
                            criar_diagrama_guindaste(
                                st.session_state.raio_max, 
                                st.session_state.extensao_lanca, 
                                resultado_calc['carga_total'], 
                                st.session_state.capacidade_raio, 
                                st.session_state.angulo_minimo_input
                            ), 
                            use_container_width=True
                        )

                        # Tabelas e métricas
                        col_tabela, col_metricas = st.columns(2)
                        with col_tabela:
                            st.dataframe(pd.DataFrame({
                                'Descrição': [
                                    'Peso Carga', 
                                    'Margem (%)', 
                                    'Peso Segurança', 
                                    'Peso Acessórios', 
                                    'Peso Cabos (3%)', 
                                    'CARGA TOTAL'
                                ],
                                'Valor (kg)': [
                                    f"{resultado_calc.get('peso_carga', 0):.2f}",
                                    f"{resultado_calc.get('margem_seguranca_percentual', 0):.2f}",
                                    f"{resultado_calc.get('peso_seguranca', 0):.2f}",
                                    f"{resultado_calc.get('peso_acessorios', 0):.2f}",
                                    f"{resultado_calc.get('peso_cabos', 0):.2f}",
                                    f"**{resultado_calc.get('carga_total', 0):.2f}**"
                                ]
                            }), hide_index=True)
                        
                        with col_metricas:
                            detalhes = validacao.get('detalhes', {})
                            st.metric("Ângulo da Lança", f"{detalhes.get('angulo_lanca', 0):.1f}°")
                            st.metric("Utilização no Raio", f"{detalhes.get('porcentagem_raio', 0):.1f}%")
                            st.metric("Utilização na Lança", f"{detalhes.get('porcentagem_alcance', 0):.1f}%")
                
                except ValueError as e:
                    st.error(f"⚠️ Erro de Validação: {e}")
                    logging.error(f"ValueError no cálculo: {e}")
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro inesperado: {e}")
                    logging.exception("Erro inesperado no cálculo de içamento")
                    with st.expander("Detalhes técnicos do erro"):
                        st.code(str(e))

    # --- ABA 2: INFORMAÇÕES E DOCUMENTOS ---
    with tab2:
        st.header("Informações e Documentos do Guindauto")
        st.info(f"ID da Avaliação: **{st.session_state.id_avaliacao}**")
        
        uploader = GoogleDriveUploader()
        ai_processor = PDFQA()
        
        st.subheader("📋 Dados da Empresa")
        col_c1, col_c2 = st.columns(2)
        with col_c1: 
            st.text_input("Empresa", key="empresa_form")
            st.text_input("CNPJ", key="cnpj_form")
        with col_c2: 
            st.text_input("Telefone", key="telefone_form")
            st.text_input("Email", key="email_form")

        st.subheader("👤 Dados do Operador")
        st.file_uploader(
            "1. Upload da CNH (.pdf, .png)", 
            key="cnh_doc_file",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Apenas arquivos PDF ou imagens PNG/JPG"
        )
        
        if st.session_state.get('cnh_doc_file') and st.button("2. Extrair e Validar CNH com IA", key="cnh_button"):
            with st.spinner("Processando CNH com IA..."):
                extracted = ai_processor.extract_structured_data(
                    st.session_state.cnh_doc_file, 
                    get_cnh_prompt()
                )
                if extracted:
                    st.session_state.operador_form = extracted.get('nome', st.session_state.operador_form)
                    st.session_state.cpf_form = extracted.get('cpf', st.session_state.cpf_form)
                    st.session_state.cnh_form = extracted.get('numero_cnh', st.session_state.cnh_form)
                    st.session_state.cnh_validade_form = extracted.get('validade_cnh', st.session_state.cnh_validade_form)
                    st.session_state.cnh_status = extracted.get('status', 'Falha na verificação')
                    st.rerun()
        
        col_op1, col_op2 = st.columns(2)
        with col_op1: 
            st.text_input("Nome", key="operador_form", disabled=True)
            st.text_input("CPF", key="cpf_form", disabled=True)
        with col_op2: 
            st.text_input("Nº da CNH", key="cnh_form", disabled=True)
            st.text_input("Validade CNH", key="cnh_validade_form", disabled=True)
        display_status(st.session_state.get('cnh_status'))

        st.subheader("🏗️ Dados do Equipamento")
        st.file_uploader(
            "Upload do CRLV (.pdf)", 
            key="crlv_file",
            type=['pdf'],
            help="Apenas arquivos PDF"
        )
        
        if st.session_state.get('crlv_file') and st.button("🔍 Extrair Dados do CRLV", key="crlv_button"):
            with st.spinner("Processando CRLV com IA..."):
                extracted = ai_processor.extract_structured_data(
                    st.session_state.crlv_file, 
                    get_crlv_prompt()
                )
                if extracted: 
                    st.session_state.placa_form = extracted.get('placa', st.session_state.placa_form)
                    st.session_state.ano_form = extracted.get('ano_fabricacao', st.session_state.ano_form)
                    st.session_state.modelo_form = extracted.get('marca_modelo', st.session_state.modelo_form)
                    st.rerun()
        
        col_e1, col_e2 = st.columns(2)
        with col_e1: 
            st.text_input("Placa", key="placa_form")
            st.text_input("Modelo", key="modelo_form")
        with col_e2: 
            st.text_input("Fabricante", key="fabricante_form")
            st.text_input("Ano", key="ano_form")

        st.subheader("📄 Documentação e Validades")
        col_d1, col_d2, col_d3 = st.columns(3)
        
        with col_d1:
            st.markdown("**ART**")
            st.file_uploader(
                "Doc. ART (.pdf)", 
                key="art_file",
                type=['pdf'],
                label_visibility="collapsed"
            ) 
            if st.session_state.get('art_file') and st.button("Verificar ART", key="art_button"):
                with st.spinner("Verificando ART..."):
                    extracted = ai_processor.extract_structured_data(
                        st.session_state.art_file, 
                        get_art_prompt()
                    )
                    if extracted: 
                        st.session_state.art_num_form = extracted.get('numero_art', st.session_state.art_num_form)
                        st.session_state.art_validade_form = extracted.get('validade_art', st.session_state.art_validade_form)
                        st.session_state.art_status = extracted.get('status', 'Falha na verificação')
                        st.rerun()
            st.text_input("Nº ART", key="art_num_form")
            st.text_input("Validade ART", key="art_validade_form", disabled=True)
            display_status(st.session_state.get('art_status'))
        
        with col_d2:
            st.markdown("**Certificação NR-11**")
            st.file_uploader(
                "Cert. NR-11 (.pdf)", 
                key="nr11_file",
                type=['pdf'],
                label_visibility="collapsed"
            ) 
            if st.session_state.get('nr11_file') and st.button("Verificar NR-11", key="nr11_button"): 
                with st.spinner("Verificando NR-11..."):
                    extracted = ai_processor.extract_structured_data(
                        st.session_state.nr11_file, 
                        get_nr11_prompt()
                    )
                    if extracted:
                        st.session_state.nr11_modulo_form = extracted.get('modulo', st.session_state.nr11_modulo_form)
                        st.session_state.nr11_validade_form = extracted.get('validade_nr11', st.session_state.nr11_validade_form)
                        st.session_state.nr11_status = extracted.get('status', 'Falha na verificação')
                        st.rerun()
            modulos_nr11 = ["", "Guindauto", "Guindaste", "Munck"]
            if st.session_state.nr11_modulo_form and st.session_state.nr11_modulo_form not in modulos_nr11: 
                modulos_nr11.append(st.session_state.nr11_modulo_form)
            st.selectbox("Módulo NR-11", options=modulos_nr11, key="nr11_modulo_form")
            st.text_input("Validade NR-11", key="nr11_validade_form", disabled=True)
            display_status(st.session_state.get('nr11_status'))
        
        with col_d3:
            st.markdown("**Manutenção (M_PREV)**")
            st.file_uploader(
                "Doc. M_PREV (.pdf)", 
                key="mprev_file",
                type=['pdf'],
                label_visibility="collapsed"
            ) 
            if st.session_state.get('mprev_file') and st.button("Verificar Manutenção", key="mprev_button"): 
                with st.spinner("Verificando Manutenção..."):
                    extracted = ai_processor.extract_structured_data(
                        st.session_state.mprev_file, 
                        get_mprev_prompt()
                    )
                    if extracted: 
                        st.session_state.mprev_data_form = extracted.get('data_ultima_manutencao', st.session_state.mprev_data_form)
                        st.session_state.mprev_prox_form = extracted.get('data_proxima_manutencao', st.session_state.mprev_prox_form)
                        st.session_state.mprev_status = extracted.get('status', 'Falha na verificação')
                        st.rerun()
            st.text_input("Última Manutenção", key="mprev_data_form", disabled=True)
            st.text_input("Próxima Manutenção", key="mprev_prox_form", disabled=True)
            display_status(st.session_state.get('mprev_status'))
        
        st.subheader("Upload de Gráfico de Carga")
        st.file_uploader(
            "Gráfico de Carga (.pdf, .png)", 
            key="grafico_carga_file",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            label_visibility="collapsed"
        ) 
        st.text_area("Observações Adicionais", key="obs_form")
        
        st.divider()
       
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Salvar Todas as Informações", type="primary", use_container_width=True):
                if not st.session_state.dados_icamento:
                    st.error("❌ Calcule os dados de içamento na Aba 1 primeiro.")
                else:
                    with st.spinner("Realizando upload de arquivos e salvando dados..."):
                        try:
                            id_avaliacao = st.session_state.id_avaliacao
                            uploads = {}
                            
                            # Upload dos arquivos
                            files_to_upload = [
                                ('cnh_doc_file', 'cnh_doc', 'cnh_doc'),
                                ('crlv_file', 'crlv', 'crlv'),
                                ('art_file', 'art_doc', 'art_doc'),
                                ('nr11_file', 'nr11_doc', 'nr11_doc'),
                                ('mprev_file', 'mprev_doc', 'mprev_doc'),
                                ('grafico_carga_file', 'grafico_doc', 'grafico_doc')
                            ]
                            
                            for state_key, upload_key, doc_type in files_to_upload:
                                if st.session_state.get(state_key):
                                    result = handle_upload_with_id(
                                        uploader, 
                                        st.session_state[state_key], 
                                        doc_type, 
                                        id_avaliacao
                                    )
                                    if result and result.get('success'):
                                        uploads[upload_key] = result
                                    else:
                                        st.warning(f"Falha no upload de {doc_type}")
                            
                            # Função auxiliar para obter URLs
                            get_url = lambda key: uploads.get(key, {}).get('url', '')
                            
                            # Preparar linha de dados do guindauto
                            dados_guindauto_row = [
                                id_avaliacao,
                                st.session_state.empresa_form,
                                st.session_state.cnpj_form,
                                st.session_state.telefone_form,
                                st.session_state.email_form,
                                st.session_state.operador_form,
                                st.session_state.cpf_form,
                                st.session_state.cnh_form,
                                st.session_state.cnh_validade_form,
                                st.session_state.nr11_modulo_form,
                                st.session_state.placa_form,
                                st.session_state.modelo_form,
                                st.session_state.fabricante_form,
                                st.session_state.ano_form,
                                st.session_state.mprev_data_form,
                                st.session_state.mprev_prox_form,
                                st.session_state.art_num_form,
                                st.session_state.art_validade_form,
                                st.session_state.obs_form,
                                get_url('art_doc'),
                                get_url('nr11_doc'),
                                get_url('cnh_doc'),
                                get_url('crlv'),
                                get_url('mprev_doc'),
                                get_url('grafico_doc')
                            ]
                            
                            # Preparar linha de dados de içamento
                            d_icamento = st.session_state.dados_icamento
                            v_icamento = d_icamento.get('validacao', {})
                            det_icamento = v_icamento.get('detalhes', {})
                            
                            dados_icamento_row = [
                                id_avaliacao,
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                d_icamento.get('peso_carga', 0),
                                d_icamento.get('margem_seguranca_percentual', 0),
                                d_icamento.get('peso_seguranca', 0),
                                d_icamento.get('peso_cabos', 0),
                                d_icamento.get('peso_acessorios', 0),
                                d_icamento.get('carga_total', 0),
                                v_icamento.get('adequado', False),
                                f"{det_icamento.get('porcentagem_raio', 0):.1f}%",
                                f"{det_icamento.get('porcentagem_alcance', 0):.1f}%",
                                d_icamento.get('fabricante_guindaste', ''),
                                d_icamento.get('nome_guindaste', ''),
                                d_icamento.get('modelo_guindaste', ''),
                                d_icamento.get('raio_max', 0),
                                d_icamento.get('capacidade_raio', 0),
                                d_icamento.get('extensao_lanca', 0),
                                d_icamento.get('capacidade_alcance', 0),
                                d_icamento.get('angulo_minimo_fabricante', 40)
                            ]

                            # Salvar nas planilhas
                            try:
                                uploader.append_data_to_sheet(LIFTING_SHEET_NAME, dados_icamento_row)
                                uploader.append_data_to_sheet(CRANE_SHEET_NAME, dados_guindauto_row)
                                
                                st.success(f"✅ Operação registrada com sucesso! ID: {id_avaliacao}")
                                st.balloons()
                                
                                # Limpeza da sessão
                                keys_to_clear = [
                                    k for k in st.session_state.keys() 
                                    if 'form' in k or '_file' in k or 'id_avaliacao' in k 
                                    or 'dados_icamento' in k or 'status' in k
                                    or k in ['peso_carga', 'peso_acessorios', 'raio_max', 
                                             'capacidade_raio', 'extensao_lanca', 
                                             'capacidade_alcance', 'fabricante_guindaste_calc',
                                             'nome_guindaste_calc']
                                ]
                                
                                for key in keys_to_clear:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                
                                time.sleep(2)
                                st.rerun()
                                
                            except Exception as sheet_error:
                                st.error(f"❌ Erro ao salvar nos registros: {sheet_error}")
                                logging.exception("Erro ao salvar nas planilhas")
                                with st.expander("Detalhes do erro"):
                                    st.code(str(sheet_error))
                                    
                        except Exception as e:
                            st.error(f"❌ Erro durante o processo de salvamento: {e}")
                            logging.exception("Erro no processo de salvamento")
                            with st.expander("Detalhes técnicos"):
                                st.code(str(e))
        
        with col_s2:
            if st.button("🔄 Limpar Formulário", use_container_width=True):
                keys_to_clear = [
                    k for k in st.session_state.keys() 
                    if 'form' in k or '_file' in k or 'id_avaliacao' in k 
                    or 'dados_icamento' in k or 'status' in k
                    or k in ['peso_carga', 'peso_acessorios', 'raio_max', 
                             'capacidade_raio', 'extensao_lanca', 
                             'capacidade_alcance', 'fabricante_guindaste_calc',
                             'nome_guindaste_calc']
                ]
                
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.warning("⚠️ Formulário limpo com sucesso!")
                time.sleep(1)
                st.rerun()
