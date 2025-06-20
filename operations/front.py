import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, date
import time
from operations.calc import calcular_carga_total, validar_guindaste
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from AI.api_Operation import PDFQA
from utils.prompts import get_crlv_prompt, get_art_prompt, get_cnh_prompt, get_nr11_prompt, get_mprev_prompt
import logging

logging.basicConfig(level=logging.INFO)

# --------------------- Funções Utilitárias --------------------

def mostrar_instrucoes():
    with st.expander("📖 Como usar este aplicativo", expanded=False):
        st.markdown("""### Guia de Uso
        
        1. **Dados da Carga**:
           * Digite o peso da carga principal em kg
           * Selecione se o equipamento é novo ou usado
             - Novo: aplica margem de segurança de 10%
             - Usado: aplica margem de segurança de 25%
           * Informe o peso dos acessórios (cintas, grilhetas, etc.)
           * O peso dos cabos será calculado automaticamente (3%)
        
        2. **Dados do Guindaste**:
           * Preencha as informações do fabricante e modelo
           * Informe o raio máximo e sua capacidade
           * Informe a extensão máxima da lança e sua capacidade
        
        3. **Resultados**:
           * O sistema calculará automaticamente:
             - Margem de segurança
             - Peso total a considerar
             - Peso dos cabos
             - Carga total final
           * Validará se o guindaste é adequado
           * Mostrará as porcentagens de utilização
        
        ⚠️ **Importante**: Se a utilização ultrapassar 80%, será necessária aprovação da engenharia e segurança.
        
        4. **Aba "Dados do Içamento"**: Preencha os dados da carga e do guindaste e clique em **Calcular**.
        5. **Aba "Informações e Documentos"**:
            - **Dados do Operador**: Faça o upload da CNH e clique em "Extrair Dados" para preencher as informações do operador.
            - **Dados do Equipamento**: Faça o upload do CRLV para preencher os dados do veículo.
            - **Preenchimento Manual**: Preencha ou corrija os demais campos necessários.
            - **Documentos**: Faça o upload de todos os outros documentos solicitados.
        6. **Salvar**: Após conferir tudo, clique em **"💾 Salvar Todas as Informações"** para registrar a operação completa.
        """)

def criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo_fabricante):
    """
    Cria um diagrama técnico avançado do guindaste com simulação de içamento.
    """
    fig = go.Figure()

    # --- Validações e Cálculos Iniciais ---
    if not all([raio_max > 0, alcance_max > 0]):
        # Retorna uma figura vazia com uma mensagem se os dados forem inválidos
        fig.update_layout(
            title="Dados insuficientes para gerar o diagrama",
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': "Por favor, insira valores válidos para Raio e Alcance.",
                'xref': "paper", 'yref': "paper",
                'showarrow': False, 'font': {'size': 16}
            }]
        )
        return fig

    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2)
    angulo_operacao_rad = np.arctan2(alcance_max, raio_max)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)

 
    fig.add_trace(go.Scatter(
        x=[-2, 2, 2, -2, -2], y=[-1, -1, 0, 0, -1],
        mode='lines', name='Base', line=dict(color='darkgray', width=4), fill='toself',
        fillcolor='lightgray', hoverinfo='none'
    ))
    # Torre do Guindaste
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[0, 2],
        mode='lines', name='Torre', line=dict(color='dimgray', width=8), hoverinfo='none'
    ))

  
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    fig.add_trace(go.Scatter(
        x=[0, raio_max], y=[2, alcance_max + 2], 
        mode='lines+markers',
        name='Lança de Operação',
        line=dict(color=cor_lanca, width=10),
        marker=dict(symbol='circle', size=8, color=cor_lanca),
        hovertemplate=f"<b>Lança de Operação</b><br>Comprimento: {comprimento_lanca:.2f} m<br>Ângulo: {angulo_operacao_graus:.2f}°<extra></extra>"
    ))

   
    angulo_min_rad = np.radians(angulo_minimo_fabricante)
    theta_risco = np.linspace(0, angulo_min_rad, 50)
    x_risco = (comprimento_lanca + 2) * np.cos(theta_risco)
    y_risco = (comprimento_lanca + 2) * np.sin(theta_risco) + 2
    fig.add_trace(go.Scatter(
        x=np.concatenate([[0], x_risco, [0]]),
        y=np.concatenate([[2], y_risco, [2]]),
        mode='lines', fill='toself', fillcolor='rgba(220, 20, 60, 0.15)',
        line=dict(color='rgba(220, 20, 60, 0.3)'),
        name=f'Zona de Risco (< {angulo_minimo_fabricante}°)',
        hoverinfo='none'
    ))
    

    fig.add_trace(go.Scatter(
        x=[0, raio_max], y=[-0.5, -0.5],
        mode='lines', name='Raio', line=dict(color='black', dash='dash', width=1),
        hoverinfo='none'
    ))
    fig.add_annotation(
        x=raio_max / 2, y=-0.5, text=f"<b>Raio: {raio_max:.2f} m</b>",
        showarrow=False, yshift=-15, font=dict(color='black', size=12)
    )

 
    fig.add_trace(go.Scatter(
        x=[-0.5, -0.5], y=[0, alcance_max + 2],
        mode='lines', name='Altura', line=dict(color='black', dash='dash', width=1),
        hoverinfo='none'
    ))
    fig.add_annotation(
        x=-0.5, y=(alcance_max + 2) / 2, text=f"<b>Altura: {alcance_max + 2:.2f} m</b>",
        showarrow=False, xshift=-45, font=dict(color='black', size=12), textangle=-90
    )

  
    fig.add_trace(go.Scatter(
        x=[raio_max], y=[alcance_max + 2],
        mode='markers', name='Ponto de Içamento',
        marker=dict(symbol='circle-open', size=15, color='darkorange', line=dict(width=3)),
        hovertemplate=f"<b>Carga Total: {carga_total:,.2f} kg</b><br>Capacidade no Raio: {capacidade_raio:,.2f} kg<extra></extra>"
    ))
    
    
    theta_arco = np.linspace(0, angulo_operacao_rad, 50)
    x_arco = (comprimento_lanca * 0.2) * np.cos(theta_arco)
    y_arco = (comprimento_lanca * 0.2) * np.sin(theta_arco) + 2
    fig.add_trace(go.Scatter(
        x=x_arco, y=y_arco, mode='lines',
        line=dict(color='darkgreen', width=2),
        hoverinfo='none'
    ))
    fig.add_annotation(
        x=x_arco[-1] * 1.2, y=y_arco[-1], text=f"<b>{angulo_operacao_graus:.1f}°</b>",
        showarrow=False, font=dict(color='darkgreen', size=14)
    )
    
   
    fig.update_layout(
        title=dict(text="<b>Diagrama Técnico da Operação de Içamento</b>", font=dict(size=20), x=0.5),
        xaxis_title="Distância Horizontal (Raio) [m]",
        yaxis_title="Altura Vertical [m]",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            range=[-5, max(raio_max, 10) * 1.1],
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            range=[-2, max(alcance_max + 2, 10) * 1.1],
            scaleanchor="x",
            scaleratio=1,
            gridcolor='lightgrey'
        ),
        margin=dict(l=80, r=40, t=80, b=80),
        hovermode='closest',
        plot_bgcolor='white' 
    )

    return fig

def gerar_id_avaliacao():
    return f"AV{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

def handle_upload_with_id(uploader, arquivo, tipo_doc, id_avaliacao):
    if arquivo is None: return None
    extensao = arquivo.name.split('.')[-1]; novo_nome = f"{id_avaliacao}_{tipo_doc}.{extensao}"
    try:
        file_url = uploader.upload_file(arquivo, novo_nome)
        return {'success': True, 'url': file_url, 'nome': novo_nome}
    except Exception as e:
        st.error(f"Erro no upload de '{novo_nome}': {e}"); return {'success': False, 'error': str(e)}

def display_status(status_text):
    if not status_text: return
    status_lower = status_text.lower()
    if "válido" in status_lower or "em dia" in status_lower:
        st.success(f"Status: {status_text}")
    elif "vencido" in status_lower:
        st.error(f"Status: {status_text}")
    else:
        st.warning(f"Status: {status_text}")

# --------------------- Página Principal --------------------
def front_page():
    # Inicialização do session_state
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
    if 'uploads' not in st.session_state: st.session_state.uploads = {}
    
    st.title("Calculadora de Movimentação de Carga")
    mostrar_instrucoes()
    
    tab1, tab2 = st.tabs(["📝 Dados do Içamento", "🏗️ Informações e Documentos"])

    # --- ABA 1: CÁLCULO DE IÇAMENTO ---
    with tab1:
        col1_estado, col2_estado = st.columns(2)
        with col1_estado:
            estado_equipamento = st.radio("Estado do Equipamento", ["Novo", "Usado"], key="estado_equip_radio", help="Novo: 10% de margem. Usado: 25%.")
        if estado_equipamento == "Novo": st.info("Margem de segurança aplicada: 10%")
        else: st.warning("Margem de segurança aplicada: 25%")
        with st.form("formulario_carga"):
            col1, col2 = st.columns(2);
            with col1:
                peso_carga = st.number_input("Peso da carga (kg)", min_value=0.1, step=100.0)
                peso_acessorios = st.number_input("Peso dos acessórios (kg)", min_value=0.0, step=1.0)
            with col2:
                fabricante_guindaste_calc = st.text_input("Fabricante do Guindaste")
                modelo_guindaste_calc = st.text_input("Modelo do Guindaste")
            st.subheader("Capacidades do Guindaste"); col3, col4 = st.columns(2);
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
        if st.session_state.dados_icamento:
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
        st.info(f"ID da Avaliação: **{st.session_state.id_avaliacao}**")
        
        uploader = GoogleDriveUploader(); ai_processor = PDFQA()
        
        st.subheader("📋 Dados da Empresa"); col_c1, col_c2 = st.columns(2)
        with col_c1: st.text_input("Empresa", key="empresa_form"); st.text_input("CNPJ", key="cnpj_form")
        with col_c2: st.text_input("Telefone", key="telefone_form"); st.text_input("Email", key="email_form")

        st.subheader("👤 Dados do Operador"); 
        cnh_doc_file = st.file_uploader("1. Upload da CNH (.pdf, .png)", key="cnh_uploader")
        if cnh_doc_file and st.button("2. Extrair e Validar CNH com IA", key="cnh_button"):
            extracted = ai_processor.extract_structured_data(cnh_doc_file, get_cnh_prompt())
            if extracted:
                st.session_state.operador_form = extracted.get('nome', st.session_state.operador_form)
                st.session_state.cpf_form = extracted.get('cpf', st.session_state.cpf_form)
                st.session_state.cnh_form = extracted.get('numero_cnh', st.session_state.cnh_form)
                st.session_state.cnh_validade_form = extracted.get('validade_cnh', st.session_state.cnh_validade_form)
                st.session_state.cnh_status = extracted.get('status', 'Falha na verificação')
        col_op1, col_op2 = st.columns(2)
        with col_op1: st.text_input("Nome", key="operador_form", disabled=True); st.text_input("CPF", key="cpf_form", disabled=True)
        with col_op2: st.text_input("Nº da CNH", key="cnh_form", disabled=True); st.text_input("Validade CNH", key="cnh_validade_form", disabled=True)
        display_status(st.session_state.cnh_status)

        st.subheader("🏗️ Dados do Equipamento"); crlv_file = st.file_uploader("Upload do CRLV (.pdf)", key="crlv_uploader")
        if crlv_file and st.button("🔍 Extrair Dados do CRLV", key="crlv_button"):
            extracted = ai_processor.extract_structured_data(crlv_file, get_crlv_prompt())
            if extracted: 
                st.session_state.placa_form = extracted.get('placa', st.session_state.placa_form)
                st.session_state.ano_form = extracted.get('ano_fabricacao', st.session_state.ano_form)
                st.session_state.modelo_form = extracted.get('marca_modelo', st.session_state.modelo_form)
        col_e1, col_e2 = st.columns(2)
        with col_e1: st.text_input("Placa", key="placa_form"); st.text_input("Modelo", key="modelo_form")
        with col_e2: st.text_input("Fabricante", key="fabricante_form"); st.text_input("Ano", key="ano_form")

        st.subheader("📄 Documentação e Validades"); col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.markdown("**ART**"); art_file = st.file_uploader("Doc. ART (.pdf)", key="art_uploader")
            if art_file and st.button("Verificar ART", key="art_button"):
                 extracted = ai_processor.extract_structured_data(art_file, get_art_prompt())
                 if extracted: 
                    st.session_state.art_num_form = extracted.get('numero_art', st.session_state.art_num_form)
                    st.session_state.art_validade_form = extracted.get('validade_art', st.session_state.art_validade_form)
                    st.session_state.art_status = extracted.get('status', 'Falha na verificação')
            st.text_input("Nº ART", key="art_num_form"); st.text_input("Validade ART", key="art_validade_form", disabled=True); display_status(st.session_state.art_status)
        with col_d2:
            st.markdown("**Certificado NR-11**"); nr11_file = st.file_uploader("Cert. NR-11 (.pdf)", key="nr11_uploader")
            if nr11_file and st.button("Verificar NR-11", key="nr11_button"):
                extracted = ai_processor.extract_structured_data(nr11_file, get_nr11_prompt())
                if extracted:
                    st.session_state.nr11_modulo_form = extracted.get('modulo', st.session_state.nr11_modulo_form)
                    st.session_state.nr11_validade_form = extracted.get('validade_nr11', st.session_state.nr11_validade_form)
                    st.session_state.nr11_status = extracted.get('status', 'Falha na verificação')
            modulos_nr11 = ["", "Guindauto", "Guindaste", "Munck"]
            if st.session_state.nr11_modulo_form and st.session_state.nr11_modulo_form not in modulos_nr11: modulos_nr11.append(st.session_state.nr11_modulo_form)
            st.selectbox("Módulo NR-11", options=modulos_nr11, key="nr11_modulo_form")
            st.text_input("Validade NR-11", key="nr11_validade_form", disabled=True); display_status(st.session_state.nr11_status)
        with col_d3:
            st.markdown("**Manutenção (M_PREV)**"); mprev_file = st.file_uploader("Doc. M_PREV (.pdf)", key="mprev_uploader")
            if mprev_file and st.button("Verificar Manutenção", key="mprev_button"):
                extracted = ai_processor.extract_structured_data(mprev_file, get_mprev_prompt())
                if extracted: 
                    st.session_state.mprev_data_form = extracted.get('data_ultima_manutencao', st.session_state.mprev_data_form)
                    st.session_state.mprev_prox_form = extracted.get('data_proxima_manutencao', st.session_state.mprev_prox_form)
                    st.session_state.mprev_status = extracted.get('status', 'Falha na verificação')
            st.text_input("Última Manutenção", key="mprev_data_form", disabled=True); st.text_input("Próxima Manutenção", key="mprev_prox_form", disabled=True); display_status(st.session_state.mprev_status)
        
        st.subheader("Upload de Gráfico de Carga"); grafico_carga_file = st.file_uploader("Gráfico de Carga (.pdf, .png)", key="grafico_uploader", label_visibility="collapsed")
        st.text_area("Observações Adicionais", key="obs_form")
        
        st.divider()
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Salvar Todas as Informações", type="primary", use_container_width=True):
                if not st.session_state.dados_icamento: st.error("Calcule os dados de içamento na Aba 1 primeiro.")
                else:
                    with st.spinner("Realizando upload de arquivos e salvando dados..."):
                        id_avaliacao = st.session_state.id_avaliacao; uploads = {}
                        if cnh_doc_file: uploads['cnh_doc'] = handle_upload_with_id(uploader, cnh_doc_file, 'cnh_doc', id_avaliacao)
                        if crlv_file: uploads['crlv'] = handle_upload_with_id(uploader, crlv_file, 'crlv', id_avaliacao)
                        if art_file: uploads['art_doc'] = handle_upload_with_id(uploader, art_file, 'art_doc', id_avaliacao)
                        if nr11_file: uploads['nr11_doc'] = handle_upload_with_id(uploader, nr11_file, 'nr11_doc', id_avaliacao)
                        if mprev_file: uploads['mprev_doc'] = handle_upload_with_id(uploader, mprev_file, 'mprev_doc', id_avaliacao)
                        if grafico_carga_file: uploads['grafico_doc'] = handle_upload_with_id(uploader, grafico_carga_file, 'grafico_doc', id_avaliacao)
                        get_url = lambda key: uploads.get(key, {}).get('url', '') if uploads.get(key) else ''
                        
                        dados_guindauto_row = [
                            id_avaliacao, st.session_state.empresa_form, st.session_state.cnpj_form, st.session_state.telefone_form, st.session_state.email_form,
                            st.session_state.operador_form, st.session_state.cpf_form, st.session_state.cnh_form, st.session_state.cnh_validade_form,
                            st.session_state.nr11_modulo_form, st.session_state.placa_form, st.session_state.modelo_form, st.session_state.fabricante_form, st.session_state.ano_form,
                            st.session_state.mprev_data_form, st.session_state.mprev_prox_form,
                            st.session_state.art_num_form, st.session_state.art_validade_form, st.session_state.obs_form,
                            get_url('art_doc'), get_url('nr11_doc'), get_url('cnh_doc'), get_url('crlv'), get_url('mprev_doc'), get_url('grafico_doc')
                        ]
                        
                        d_icamento = st.session_state.dados_icamento; v_icamento = d_icamento.get('validacao', {}); det_icamento = v_icamento.get('detalhes', {})
                        dados_icamento_row = [id_avaliacao, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), d_icamento.get('peso_carga'), d_icamento.get('margem_seguranca_percentual'), d_icamento.get('peso_seguranca'), d_icamento.get('peso_cabos'), d_icamento.get('peso_acessorios'), d_icamento.get('carga_total'), v_icamento.get('adequado'), f"{det_icamento.get('porcentagem_raio', 0):.1f}%", f"{det_icamento.get('porcentagem_alcance', 0):.1f}%", d_icamento.get('fabricante_guindaste'), d_icamento.get('modelo_guindaste'), d_icamento.get('raio_max'), d_icamento.get('capacidade_raio'), d_icamento.get('alcance_max'), d_icamento.get('capacidade_alcance'), d_icamento.get('angulo_minimo_fabricante')]

                        try:
                            uploader.append_data_to_sheet(LIFTING_SHEET_NAME, dados_icamento_row); uploader.append_data_to_sheet(CRANE_SHEET_NAME, dados_guindauto_row)
                            st.success(f"✅ Operação registrada com ID: {id_avaliacao}")
                            keys_to_clear = [k for k in st.session_state.keys() if 'form' in k or 'upload' in k or 'id_avaliacao' in k or 'dados_icamento' in k]; 
                            for key in keys_to_clear: del st.session_state[key]
                            time.sleep(2); st.rerun()
                        except Exception as e: st.error(f"Erro ao salvar nos registros: {e}")
        with col_s2:
            if st.button("🔄 Limpar Formulário", use_container_width=True):
                keys_to_clear = [k for k in st.session_state.keys() if 'form' in k or 'upload' in k or 'id_avaliacao' in k or 'dados_icamento' in k]; 
                for key in keys_to_clear: del st.session_state[key]
                st.warning("⚠️ Formulário limpo."); st.rerun()
