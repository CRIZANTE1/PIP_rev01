# FILE: front.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import time

# Funções e classes do projeto
from operations.calc import calcular_carga_total, validar_guindaste
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from AI.api_Operation import PDFQA
from utils.prompts import get_crlv_prompt, get_art_prompt, get_cnh_prompt, get_nr11_prompt
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)

# --------------------- Funções Utilitárias --------------------

def mostrar_instrucoes():
    with st.expander("📖 Como usar este aplicativo", expanded=False):
        st.markdown("""
        ### Guia Rápido
        1. **Aba "Dados do Içamento"**: Preencha os dados da carga e do guindaste e clique em **Calcular**.
        2. **Aba "Informações e Documentos"**:
            - **Preenchimento com IA**: Use os botões **"🔍 Extrair Dados..."** para preencher campos de documentos automaticamente.
            - **Preenchimento Manual**: Preencha ou corrija todos os campos necessários.
            - **Documentos**: Faça o upload de todos os documentos solicitados. O sistema calculará as validades e preparará os arquivos para o registro final.
        3. **Salvar**: Após conferir tudo, clique em **"💾 Salvar Todas as Informações"** para registrar a operação completa.
        """)

def criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo):
    fig = go.Figure()
    if not all([raio_max > 0, alcance_max > 0]): return fig
    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2)
    angulo_atual = np.degrees(np.arctan2(alcance_max, raio_max))
    fig.add_trace(go.Scatter(x=[-2, 2, 2, -2, -2], y=[-1, -1, 0, 0, -1], mode='lines', name='Base', line=dict(color='darkgray', width=3), fill='toself'))
    cor_atual = 'blue' if angulo_minimo <= angulo_atual <= 80 else 'red'
    fig.add_trace(go.Scatter(x=[0, raio_max], y=[0, alcance_max], mode='lines', name=f'Lança Atual ({angulo_atual:.1f}°)', line=dict(color=cor_atual, width=4)))
    x_min = comprimento_lanca * np.cos(np.radians(angulo_minimo))
    y_min = comprimento_lanca * np.sin(np.radians(angulo_minimo))
    fig.add_trace(go.Scatter(x=[0, x_min], y=[0, y_min], mode='lines', name=f'Ângulo Mínimo ({angulo_minimo}°)', line=dict(color='orange', width=2, dash='dash')))
    fig.update_layout(title='Diagrama Técnico da Operação', xaxis_title='Raio (m)', yaxis_title='Altura (m)', xaxis=dict(range=[-5, raio_max + 5]), yaxis=dict(range=[-2, alcance_max + 5]), yaxis_scaleanchor="x", yaxis_scaleratio=1, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

def gerar_id_avaliacao():
    return f"AV{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

def handle_upload_with_id(uploader, arquivo, tipo_doc, id_avaliacao):
    if arquivo is None: return None
    extensao = arquivo.name.split('.')[-1]
    novo_nome = f"{id_avaliacao}_{tipo_doc}.{extensao}"
    try:
        file_url = uploader.upload_file(arquivo, novo_nome)
        return {'success': True, 'url': file_url, 'nome': novo_nome}
    except Exception as e:
        st.error(f"Erro no upload de '{novo_nome}': {e}")
        return {'success': False, 'error': str(e)}
        
def parse_date_string(date_str):
    if not date_str: return None
    try: return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except (ValueError, TypeError): return None

# --------------------- Página Principal --------------------

def front_page():
    # Inicialização correta e completa do session_state no início da função
    form_keys = [
        'empresa_form', 'cnpj_form', 'telefone_form', 'email_form', 'operador_form', 'cpf_form',
        'cnh_form', 'cnh_validade_form', 'placa_form', 'modelo_form', 'fabricante_form', 'ano_form',
        'art_num_form', 'art_validade_form', 'obs_form',
        'nr11_num_form', 'nr11_data_form', 'nr11_validade_form', 'mprev_data_form', 'mprev_prox_form'
    ]
    for key in form_keys:
        if key not in st.session_state:
            if any(s in key for s in ['date', 'validade', 'prox']): st.session_state[key] = None
            elif key == 'ano_form': st.session_state[key] = date.today().year
            else: st.session_state[key] = ""

    st.title("Calculadora de Movimentação de Carga")
    mostrar_instrucoes()
    
    tab1, tab2 = st.tabs(["📝 Dados do Içamento", "🏗️ Informações e Documentos"])

    # --- ABA 1: DADOS DO IÇAMENTO E CÁLCULO ---
    with tab1:
        col1_estado, col2_estado = st.columns(2)
        with col1_estado:
            estado_equipamento = st.radio("Estado do Equipamento", ["Novo", "Usado"], key="estado_equip_radio", help="Novo: 10% de margem. Usado: 25%.")
        if estado_equipamento == "Novo": st.info("Margem de segurança aplicada: 10%")
        else: st.warning("Margem de segurança aplicada: 25%")
        
        with st.form("formulario_carga"):
            col1, col2 = st.columns(2)
            with col1:
                peso_carga = st.number_input("Peso da carga (kg)", min_value=0.1, step=100.0)
                peso_acessorios = st.number_input("Peso dos acessórios (kg)", min_value=0.0, step=1.0)
            with col2:
                fabricante_guindaste_calc = st.text_input("Fabricante do Guindaste")
                modelo_guindaste_calc = st.text_input("Modelo do Guindaste")
            st.subheader("Capacidades do Guindaste")
            col3, col4 = st.columns(2)
            with col3:
                raio_max = st.number_input("Raio Máximo (m)", min_value=0.1, step=0.1)
                capacidade_raio = st.number_input("Capacidade no Raio Máximo (kg)", min_value=0.1, step=100.0)
            with col4:
                alcance_max = st.number_input("Extensão Máxima da Lança (m)", min_value=0.1, step=0.1)
                capacidade_alcance = st.number_input("Capacidade na Lança Máxima (kg)", min_value=0.1, step=100.0)
                angulo_minimo_fabricante = st.number_input("Ângulo Mínimo da Lança (°)", min_value=1.0, max_value=89.0, value=30.0)
            
            if st.form_submit_button("Calcular"):
                try:
                    resultado = calcular_carga_total(peso_carga, estado_equipamento=="Novo", peso_acessorios)
                    st.session_state.dados_icamento = {**resultado, 'fabricante_guindaste': fabricante_guindaste_calc, 'modelo_guindaste': modelo_guindaste_calc, 'raio_max': raio_max, 'capacidade_raio': capacidade_raio, 'alcance_max': alcance_max, 'capacidade_alcance': capacidade_alcance, 'angulo_minimo_fabricante': angulo_minimo_fabricante}
                    validacao = validar_guindaste(resultado['carga_total'], capacidade_raio, capacidade_alcance, raio_max, alcance_max)
                    st.session_state.dados_icamento['validacao'] = validacao
                    st.success("Cálculo realizado. Verifique os resultados abaixo.")
                except Exception as e: st.error(f"Erro no cálculo: {e}")

        # Exibe os resultados fora do formulário para persistirem
        if 'dados_icamento' in st.session_state:
            res = st.session_state.dados_icamento; val = res.get('validacao', {})
            st.subheader("📊 Resultados do Cálculo"); st.table(pd.DataFrame({'Descrição': ['Peso da carga', 'Margem (%)', 'Peso Segurança', 'Peso a Considerar', 'Peso Cabos (3%)', 'Peso Acessórios', 'CARGA TOTAL'], 'Valor (kg)': [f"{res.get(k, 0):.2f}" for k in ['peso_carga', 'margem_seguranca_percentual', 'peso_seguranca', 'peso_considerar', 'peso_cabos', 'peso_acessorios']] + [f"**{res.get('carga_total', 0):.2f}**"]}))
            st.subheader("🎯 Resultado da Validação"); 
            if val.get('adequado'): st.success(f"✅ {val.get('mensagem')}")
            else: st.error(f"⚠️ {val.get('mensagem', 'Falha na validação.')}")
            c1, c2 = st.columns(2); c1.metric("Utilização no Raio", f"{val.get('detalhes', {}).get('porcentagem_raio', 0):.1f}%"); c2.metric("Utilização na Lança", f"{val.get('detalhes', {}).get('porcentagem_alcance', 0):.1f}%")
            st.plotly_chart(criar_diagrama_guindaste(res['raio_max'], res['alcance_max'], res['carga_total'], res['capacidade_raio'], res['angulo_minimo_fabricante']), use_container_width=True)

    # --- ABA 2: INFORMAÇÕES E DOCUMENTOS ---
    with tab2:
        st.header("Informações e Documentos do Guindauto")
        if 'id_avaliacao' not in st.session_state: st.session_state.id_avaliacao = gerar_id_avaliacao()
        st.info(f"ID da Avaliação: **{st.session_state.id_avaliacao}**")
        
        uploader = GoogleDriveUploader()
        ai_processor = PDFQA()
        
        st.subheader("📋 Dados Cadastrais"); col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.session_state.empresa_form = st.text_input("Empresa", value=st.session_state.empresa_form, key="empresa_input")
            st.session_state.cnpj_form = st.text_input("CNPJ", value=st.session_state.cnpj_form, key="cnpj_input")
            st.session_state.operador_form = st.text_input("Nome do Operador", value=st.session_state.operador_form, key="operador_input")
            st.session_state.cpf_form = st.text_input("CPF do Operador", value=st.session_state.cpf_form, key="cpf_input")
        with col_c2:
            st.session_state.telefone_form = st.text_input("Telefone", value=st.session_state.telefone_form, key="tel_input")
            st.session_state.email_form = st.text_input("Email", value=st.session_state.email_form, key="email_input")
            st.session_state.cnh_form = st.text_input("Número da CNH", value=st.session_state.cnh_form, key="cnh_num_input")
            st.session_state.cnh_validade_form = st.date_input("Validade da CNH", value=st.session_state.cnh_validade_form, key="cnh_val_input")

        st.subheader("🏗️ Dados do Equipamento"); crlv_file = st.file_uploader("Upload do CRLV (.pdf)", type='pdf', key="crlv_uploader")
        if crlv_file and st.button("🔍 Extrair Dados do CRLV", key="extract_crlv_button"):
            extracted = ai_processor.extract_structured_data(crlv_file, get_crlv_prompt())
            if extracted:
                st.session_state.placa_form = extracted.get('placa', st.session_state.placa_form); st.session_state.ano_form = int(extracted.get('ano_fabricacao') or st.session_state.ano_form); st.session_state.modelo_form = extracted.get('marca_modelo', st.session_state.modelo_form);
                st.rerun()
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.session_state.placa_form = st.text_input("Placa Guindaste", value=st.session_state.placa_form, key="placa_input")
            st.session_state.modelo_form = st.text_input("Modelo Equipamento", value=st.session_state.modelo_form, key="modelo_input")
        with col_e2:
            st.session_state.fabricante_form = st.text_input("Fabricante Equipamento", value=st.session_state.fabricante_form, key="fab_input")
            st.session_state.ano_form = st.number_input("Ano Fabricação", min_value=1950, max_value=date.today().year + 1, value=st.session_state.ano_form, key="ano_input")

        st.subheader("📄 Documentação e Validades"); col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.markdown("**ART**"); art_file = st.file_uploader("Doc. ART (.pdf)", key="art_uploader")
            if art_file and st.button("🔍 Extrair Dados da ART", key="extract_art_button"):
                 extracted = ai_processor.extract_structured_data(art_file, get_art_prompt()); 
                 if extracted: st.session_state.art_num_form = extracted.get('numero_art', st.session_state.art_num_form); st.session_state.art_validade_form = parse_date_string(extracted.get('data_emissao')); st.rerun()
            st.session_state.art_num_form = st.text_input("Número ART", value=st.session_state.art_num_form, key="art_num_input")
            st.session_state.art_validade_form = st.date_input("Validade ART", value=st.session_state.art_validade_form, key="art_val_input")
        with col_d2:
            st.markdown("**Certificado NR-11**"); nr11_file = st.file_uploader("Cert. NR-11 (.pdf)", key="nr11_uploader")
            if nr11_file and st.button("🔍 Extrair Dados do NR-11", key="extract_nr11_button"):
                extracted = ai_processor.extract_structured_data(nr11_file, get_nr11_prompt())
                if extracted:
                    st.session_state.operador_form = extracted.get('nome_operador', st.session_state.operador_form); st.session_state.nr11_num_form = extracted.get('numero_nr11', st.session_state.nr11_num_form); st.session_state.nr11_data_form = parse_date_string(extracted.get('data_emissao')); st.session_state.nr11_validade_form = parse_date_string(extracted.get('validade')); st.rerun()
            st.session_state.nr11_num_form = st.text_input("Número NR-11", value=st.session_state.nr11_num_form, key="nr11_num_input")
            st.session_state.nr11_data_form = st.date_input("Emissão NR-11", value=st.session_state.nr11_data_form, key="nr11_data_input")
            validade_nr11 = st.session_state.nr11_validade_form if st.session_state.nr11_validade_form else (st.session_state.nr11_data_form + relativedelta(years=1) if st.session_state.nr11_data_form else None)
            if validade_nr11:
                if validade_nr11 >= date.today(): st.success(f"Válido até: {validade_nr11.strftime('%d/%m/%Y')}")
                else: st.error(f"Vencido em: {validade_nr11.strftime('%d/%m/%Y')}")
        with col_d3:
            st.markdown("**Manutenção (M_PREV)**"); mprev_file = st.file_uploader("Doc. M_PREV (.pdf)", key="mprev_uploader")
            st.session_state.mprev_data_form = st.date_input("Data Última Manut.", value=st.session_state.mprev_data_form, key="mprev_data_input")
            if st.session_state.mprev_data_form:
                st.session_state.mprev_prox_form = st.session_state.mprev_data_form + relativedelta(years=1)
                if st.session_state.mprev_prox_form >= date.today(): st.success(f"Próxima até: {st.session_state.mprev_prox_form.strftime('%d/%m/%Y')}")
                else: st.error(f"Vencida desde: {st.session_state.mprev_prox_form.strftime('%d/%m/%Y')}")

        st.subheader("Upload de Arquivos Adicionais"); col_a1, col_a2 = st.columns(2)
        with col_a1: 
            cnh_doc_file = st.file_uploader("Upload da CNH (.pdf, .png)", key="cnh_doc_uploader")
            if cnh_doc_file and st.button("🔍 Extrair Dados da CNH", key="extract_cnh_button"):
                extracted = ai_processor.extract_structured_data(cnh_doc_file, get_cnh_prompt())
                if extracted:
                    st.session_state.operador_form = extracted.get('nome', st.session_state.operador_form); st.session_state.cnh_form = extracted.get('numero_cnh', st.session_state.cnh_form); st.session_state.cnh_validade_form = parse_date_string(extracted.get('validade')); st.session_state.cpf_form = extracted.get('cpf', st.session_state.cpf_form);
                    st.rerun()
        with col_a2: 
            grafico_carga_file = st.file_uploader("Gráfico de Carga (.pdf, .png)", key="grafico_uploader")

        st.session_state.obs_form = st.text_area("Observações Adicionais", value=st.session_state.obs_form, key="obs_input")
        
        st.divider()
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Salvar Todas as Informações", type="primary", use_container_width=True):
                if 'dados_icamento' not in st.session_state: st.error("Calcule os dados de içamento na Aba 1 primeiro.")
                else:
                    with st.spinner("Realizando upload de arquivos e salvando dados..."):
                        id_avaliacao = st.session_state.id_avaliacao
                        uploads = {}
                        if crlv_file: uploads['crlv'] = handle_upload_with_id(uploader, crlv_file, 'crlv', id_avaliacao)
                        if art_file: uploads['art_doc'] = handle_upload_with_id(uploader, art_file, 'art_doc', id_avaliacao)
                        if nr11_file: uploads['nr11_doc'] = handle_upload_with_id(uploader, nr11_file, 'nr11_doc', id_avaliacao)
                        if mprev_file: uploads['mprev_doc'] = handle_upload_with_id(uploader, mprev_file, 'mprev_doc', id_avaliacao)
                        if cnh_doc_file: uploads['cnh_doc'] = handle_upload_with_id(uploader, cnh_doc_file, 'cnh_doc', id_avaliacao)
                        if grafico_carga_file: uploads['grafico_doc'] = handle_upload_with_id(uploader, grafico_carga_file, 'grafico_doc', id_avaliacao)
                        
                        get_url = lambda key: uploads.get(key, {}).get('url', '') if uploads.get(key) else ''
                        
                        dados_guindauto_row = [
                            id_avaliacao, st.session_state.empresa_form, st.session_state.cnpj_form, st.session_state.telefone_form, st.session_state.email_form,
                            st.session_state.operador_form, st.session_state.cpf_form, st.session_state.cnh_form, st.session_state.cnh_validade_form.isoformat() if st.session_state.cnh_validade_form else '',
                            st.session_state.nr11_num_form, st.session_state.placa_form, st.session_state.modelo_form, st.session_state.fabricante_form, st.session_state.ano_form,
                            st.session_state.mprev_data_form.isoformat() if st.session_state.mprev_data_form else '', st.session_state.mprev_prox_form.isoformat() if st.session_state.mprev_prox_form else '',
                            st.session_state.art_num_form, st.session_state.art_validade_form.isoformat() if st.session_state.art_validade_form else '', st.session_state.obs_form,
                            get_url('art_doc'), get_url('nr11_doc'), get_url('cnh_doc'), get_url('crlv'), get_url('mprev_doc'), get_url('grafico_doc')
                        ]
                        
                        d_icamento = st.session_state.dados_icamento; v_icamento = d_icamento.get('validacao', {}); det_icamento = v_icamento.get('detalhes', {})
                        dados_icamento_row = [id_avaliacao, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), d_icamento.get('peso_carga'), d_icamento.get('margem_seguranca_percentual'), d_icamento.get('peso_seguranca'), d_icamento.get('peso_cabos'), d_icamento.get('peso_acessorios'), d_icamento.get('carga_total'), v_icamento.get('adequado'), f"{det_icamento.get('porcentagem_raio', 0):.1f}%", f"{det_icamento.get('porcentagem_alcance', 0):.1f}%", d_icamento.get('fabricante_guindaste'), d_icamento.get('modelo_guindaste'), d_icamento.get('raio_max'), d_icamento.get('capacidade_raio'), d_icamento.get('alcance_max'), d_icamento.get('capacidade_alcance'), d_icamento.get('angulo_minimo_fabricante')]

                        try:
                            uploader.append_data_to_sheet(LIFTING_SHEET_NAME, dados_icamento_row); uploader.append_data_to_sheet(CRANE_SHEET_NAME, dados_guindauto_row)
                            st.success(f"✅ Operação registrada com ID: {id_avaliacao}"); st.balloons()
                            keys_to_clear = [k for k in st.session_state.keys() if 'form' in k or 'upload' in k or 'id_avaliacao' in k or 'dados_icamento' in k]; 
                            for key in keys_to_clear: del st.session_state[key]
                            time.sleep(3); st.rerun()
                        except Exception as e: st.error(f"Erro ao salvar nos registros: {e}")
        with col_s2:
            if st.button("🔄 Limpar Formulário", use_container_width=True):
                keys_to_clear = [k for k in st.session_state.keys() if 'form' in k or 'upload' in k or 'id_avaliacao' in k or 'dados_icamento' in k]; 
                for key in keys_to_clear: del st.session_state[key]
                st.warning("⚠️ Formulário limpo."); st.rerun()
