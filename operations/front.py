import streamlit as st
from operations.calc import calcular_carga_total, validar_guindaste
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from AI.api_Operation import PDFQA
from utils.prompts import get_crlv_prompt, get_art_prompt, get_cnh_prompt, get_nr11_prompt
import time


# --------------------- Instruções de uso --------------------
def mostrar_instrucoes():
    with st.expander("📖 Como usar este aplicativo", expanded=True):
        st.markdown("""
        ### Guia de Uso
        
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
        """)


# ------------------------------------ Diagrama ilustrativo -----------------------------------------
def criar_diagrama_guindaste(raio_max, alcance_max, carga_total=None, capacidade_raio=None, angulo_minimo=45):
    """Cria um diagrama técnico do guindaste com simulação de içamento."""
    
    fig = go.Figure()
    # Comprimento da lança é o menor entre a hipotenusa teórica e o raio_max (interpretado como um limite para o comprimento da lança no diagrama)
    comprimento_lanca = min(np.sqrt(raio_max**2 + alcance_max**2), raio_max) if raio_max > 0 else np.sqrt(alcance_max**2) # Avoid sqrt of negative if raio_max is 0
    if raio_max == 0 and alcance_max == 0: # Prevent division by zero if both are zero
        angulo_atual = 0.0
    elif raio_max == 0:
        angulo_atual = 90.0
    else:
        angulo_atual = np.degrees(np.arctan2(alcance_max, raio_max))
        
    angulo_maximo = 80  
    
    
    if carga_total and capacidade_raio and carga_total > 0: # Evitar divisão por zero
        raio_trabalho_seguro = min((capacidade_raio/carga_total) * raio_max, raio_max)
        raio_trabalho_seguro = max(raio_trabalho_seguro, raio_max * 0.2) # Mínimo de 20% do raio_max
    else:
        raio_trabalho_seguro = raio_max # Default se não houver dados de carga/capacidade

    # Garantir que raio_trabalho_seguro não exceda comprimento_lanca para evitar erro no sqrt
    # e que o argumento do sqrt seja não negativo.
    # O ângulo de trabalho é calculado com base no raio seguro e no comprimento da lança.
    if comprimento_lanca == 0: # Avoid division by zero / invalid ops if lanca is 0
        angulo_trabalho = 0.0
    else:
        # Ensure raio_trabalho_seguro does not exceed comprimento_lanca for sqrt
        raio_para_calculo_angulo = min(raio_trabalho_seguro, comprimento_lanca)
        argumento_sqrt = comprimento_lanca**2 - raio_para_calculo_angulo**2
        altura_segura_calculada = np.sqrt(max(0, argumento_sqrt)) # max(0,...) para evitar erro de sqrt de negativo pequeno
        
        if raio_para_calculo_angulo == 0 and altura_segura_calculada == 0:
             angulo_trabalho = 0.0
        elif raio_para_calculo_angulo == 0:
             angulo_trabalho = 90.0 # Lança vertical
        else:
            angulo_trabalho = np.degrees(np.arctan2(
                altura_segura_calculada,
                raio_para_calculo_angulo
            ))
    
    
    angulo_seguro = min(max(angulo_minimo, angulo_trabalho), angulo_maximo)
    
    # Coordenadas da posição atual da lança
    x_atual = comprimento_lanca * np.cos(np.radians(angulo_atual))
    y_atual = comprimento_lanca * np.sin(np.radians(angulo_atual))
    
    # Coordenadas da posição segura da lança
    x_seguro = comprimento_lanca * np.cos(np.radians(angulo_seguro))
    y_seguro = comprimento_lanca * np.sin(np.radians(angulo_seguro))

    fig.add_trace(go.Scatter(
        x=[0, x_seguro],
        y=[0, y_seguro],
        mode='lines',
        name=f'Posição Segura ({angulo_seguro:.1f}°)',
        line=dict(color='green', width=2, dash='dash'),
        hovertemplate=f'<b>Ângulo Seguro:</b> {angulo_seguro:.1f}°<extra></extra>'
    ))
    
  
    fig.add_trace(go.Scatter(
        x=[-2, 2, 2, -2, -2],
        y=[-1, -1, 0, 0, -1],
        mode='lines',
        name='Base do Guindaste',
        line=dict(color='darkgray', width=3),
        fill='toself'
    ))
    
    
    cor_atual = 'blue' if angulo_minimo <= angulo_atual <= angulo_maximo else 'red'
    fig.add_trace(go.Scatter(
        x=[0, x_atual],
        y=[0, y_atual],
        mode='lines',
        name=f'Posição Atual ({angulo_atual:.1f}°)',
        line=dict(color=cor_atual, width=3),
        hovertemplate=f'Ângulo: {angulo_atual:.1f}°<extra></extra>'
    ))
    
    
    theta = np.linspace(np.radians(angulo_maximo), np.pi/2, 50)
    # Zona de perigo (sobre o guindaste) usa o comprimento da lança
    x_zona = comprimento_lanca * np.cos(theta)
    y_zona = comprimento_lanca * np.sin(theta)
    fig.add_trace(go.Scatter(
        x=np.concatenate([[0], x_zona, [0]]),
        y=np.concatenate([[0], y_zona, [0]]),
        fill='toself',
        fillcolor='rgba(255,0,0,0.1)',
        name='Zona de Perigo (Sobre o Guindaste)',
        line=dict(color='red', width=1, dash='dot'),
        hovertemplate='<b>Zona de Perigo</b><br>Ângulo > 80°<extra></extra>'
    ))

 
    fig.add_annotation(
        x=max(raio_max, comprimento_lanca) * 0.3,  # Ajustar posição da anotação baseada no maior entre raio_max e compr_lanca
        y=max(alcance_max, comprimento_lanca) * 0.8,  
        text=f"Ângulo de Perigo: {angulo_maximo}°",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        arrowsize=1,
        arrowwidth=2,
        ax=50,  
        ay=-30, 
        font=dict(
            color="red",
            size=12
        ),
        align="left"
    )

  
    # Coordenadas do ângulo mínimo
    x_min = comprimento_lanca * np.cos(np.radians(angulo_minimo))
    y_min = comprimento_lanca * np.sin(np.radians(angulo_minimo))
    fig.add_trace(go.Scatter(
        x=[0, x_min],
        y=[0, y_min],
        mode='lines',
        name=f'Ângulo Mínimo ({angulo_minimo}°)',
        line=dict(color='orange', width=2, dash='dash'),
        hovertemplate=f'<b>Ângulo Mínimo:</b> {angulo_minimo}°<extra></extra>'
    ))

    
    fig.update_layout(
        title=dict(
            text='Diagrama do Guindaste',
            x=0.5,
            y=0.95,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis_title='Distância (m)',
        yaxis_title='Altura (m)',
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(0,0,0,0)',  
            bordercolor='rgba(0,0,0,0)',  
            font=dict(
                size=12,
                # color='white' # Consider removing if not using dark theme, or make conditional
            )
        ),
        xaxis=dict(
            range=[-2, max(raio_max, comprimento_lanca) + 1], # Ajustar range
            dtick=1 if max(raio_max, comprimento_lanca) < 20 else 5, # Ajustar dtick dinamicamente
            tick0=0,
            title=dict(
                text='Distância (m)',
                font=dict(size=14),
                standoff=10
            ),
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(0, 0, 0, 0.5)',
            zerolinewidth=1
        ),
        yaxis=dict(
            range=[-2, max(alcance_max, comprimento_lanca) + 2], # Ajustar range
            title=dict(
                text='Altura (m)',
                font=dict(size=14),
                standoff=10
            ),
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(0, 0, 0, 0.5)',
            zerolinewidth=1
        ),
        yaxis_scaleanchor="x",
        yaxis_scaleratio=1,
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.8)", # Light background for better readability
            font_size=12,
            font_family="Arial"
        ),
        margin=dict(t=100, l=80, r=80, b=80),
        width=800,
        height=600
    )

    return fig

def gerar_id_avaliacao():
    """Gera um ID único para a avaliação"""
    return f"AV{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

def handle_upload_with_id(uploader, arquivo, tipo_doc, id_avaliacao):
    """
    Gerencia o upload de arquivos com ID único
    
    Args:
        uploader: Instância do GoogleDriveUploader
        arquivo: Arquivo para upload
        tipo_doc: Tipo do documento (ex: 'grafico', 'art', 'cert')
        id_avaliacao: ID único da avaliação
    """
    if arquivo is not None:
        nome_original = arquivo.name
        extensao = nome_original.split('.')[-1]
        novo_nome = f"{id_avaliacao}_{tipo_doc}.{extensao}"
        
        try:
            file_url = uploader.upload_file(arquivo, novo_nome)
            return {
                'success': True,
                'url': file_url,
                'nome': novo_nome
            }
        except Exception as e:
            st.error(f"Erro no upload do arquivo '{novo_nome}': {e}") # Adicionado para depuração
            return {
                'success': False,
                'error': str(e)
            }
    return None


def front_page():
    # Inicialização completa do session_state para todos os campos
    form_keys = [
        'empresa_responsavel_form', 'cnpj_form', 'telefone_form', 'email_form',
        'nome_operador_form', 'cpf_operador_form', 'cnh_form', 'validade_cnh_form',
        'placa_equip_form', 'modelo_equip_form', 'fabricante_equip_form', 'ano_equip_form',
        'ultima_manutencao_form', 'proxima_manutencao_form',
        'num_art_form', 'validade_art_form', 'observacoes_form',
        'nr11_data_emissao_form', 'mprev_data_emissao_form'
    ]
    for key in form_keys:
        if key not in st.session_state:
            if key == 'ano_equip_form': st.session_state[key] = datetime.now().year
            elif 'date' in key or 'manutencao' in key: st.session_state[key] = None
            else: st.session_state[key] = ""

    st.title("Calculadora de Movimentação de Carga")
    mostrar_instrucoes()
    
    tab1, tab2 = st.tabs(["📝 Dados do Içamento", "🏗️ Informações e Documentos"])

    with tab1:
        
        col1_estado, col2_estado = st.columns(2) # Renomeadas para evitar conflito com colunas do form
        
        with col1_estado:
          
            estado_equipamento = st.radio(
                "Estado do Equipamento",
                options=["Novo", "Usado"],
                index=0, # Default para Novo
                key="estado_equipamento_radio", # Adicionar key para unicidade
                help="Escolha 'Novo' para 10% de margem ou 'Usado' para 25%"
            )
            
          
            if estado_equipamento == "Novo":
                st.info("⚠️ Margem de segurança: 10% (equipamento novo)")
            else:
                st.warning("⚠️ Margem de segurança: 25% (equipamento usado)")

       
        with st.form("formulario_carga"):
            col1_form, col2_form = st.columns(2) # Renomeadas para evitar conflito
            
            with col1_form:
                peso_carga = st.number_input(
                    "Peso da carga (kg)",
                    min_value=0.0,
                    step=100.0,
                    value=0.0, # Default value
                    help=" Peso do objeto principal a ser içado, sem incluir acessórios ou cabos"
                )

            with col2_form:
                peso_acessorios = st.number_input(
                    "Peso dos acessórios (kg)",
                    min_value=0.0,
                    step=1.0,
                    value=0.0, # Default value
                    help="Peso total de todos os equipamentos auxiliares como cintas, grilhetas, manilhas, etc."
                )
                
            st.info("ℹ️ O peso dos cabos será calculado automaticamente como 3% do peso a considerar")

            
            st.subheader("Dados do Guindaste (para cálculo)")
            col3_form, col4_form = st.columns(2) # Renomeadas para evitar conflito
            
            with col3_form:
                fabricante_guindaste_calc = st.text_input( # Variável com nome específico
                    "Fabricante do Guindaste (para cálculo)",
                    help=" Nome da empresa que fabricou o guindaste (ex: Liebherr, Manitowoc, etc.)"
                )
                modelo_guindaste_calc = st.text_input( # Variável com nome específico
                    "Modelo do Guindaste (para cálculo)",
                    help=" Código ou nome do modelo específico do guindaste (ex: LTM 1100, GMK 5220)"
                )
                
                raio_max = st.number_input(
                    "Raio Máximo (m)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0, # Default value
                    help=" Distância horizontal máxima do centro do guindaste até o ponto de içamento"
                )

            with col4_form:
                capacidade_raio = st.number_input(
                    "Capacidade no Raio Máximo (kg)",
                    min_value=0.0,
                    step=100.0,
                    value=0.0, # Default value
                    help=" Peso máximo que o guindaste pode levantar na distância horizontal especificada"
                )
                
                alcance_max = st.number_input(
                    "Extensão Máxima da Lança (m)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0, # Default value
                    help=" Comprimento total da lança quando totalmente estendida"
                )
                
                capacidade_alcance = st.number_input(
                    "Capacidade na Lança Máxima (kg)",
                    min_value=0.0,
                    step=100.0,
                    value=0.0, # Default value
                    help=" Peso máximo que o guindaste pode levantar com a lança totalmente estendida"
                )
                
                angulo_minimo_fabricante = st.number_input(
                    "Ângulo Mínimo da Lança (graus)",
                    min_value=0.0,
                    max_value=89.0, # Max < 90
                    value=30.0, # Default value
                    step=1.0,
                    help=" Menor ângulo permitido entre a lança e o solo, conforme manual do fabricante"
                )

            submeter = st.form_submit_button("Calcular")

        if submeter: # Processar somente se o botão for clicado
            if peso_carga <= 0:
                st.warning("⚠️ Por favor, insira um peso da carga válido para realizar os cálculos.")
            else:
                try:
                    is_novo = estado_equipamento == "Novo"
                    resultado = calcular_carga_total(peso_carga, is_novo, peso_acessorios)
                    
                    st.session_state.dados_icamento = {
                        'peso_carga': resultado['peso_carga'],
                        'margem_seguranca_percentual': 10 if is_novo else 25,
                        'peso_seguranca': resultado['peso_seguranca'],
                        'peso_considerar': resultado['peso_considerar'],
                        'peso_cabos': resultado['peso_cabos'],
                        'peso_acessorios': resultado['peso_acessorios'],
                        'carga_total': resultado['carga_total'],
                        'fabricante_guindaste': fabricante_guindaste_calc, # Usar variável específica
                        'modelo_guindaste': modelo_guindaste_calc, # Usar variável específica
                        'raio_max': raio_max,
                        'capacidade_raio': capacidade_raio,
                        'alcance_max': alcance_max,
                        'capacidade_alcance': capacidade_alcance,
                        'angulo_minimo_fabricante': angulo_minimo_fabricante
                    }

                    st.subheader("📊 Resultados do Cálculo")
                    
                    # Usar pd.DataFrame para melhor formatação da tabela
                    df_resultados = pd.DataFrame({
                        'Descrição': [
                            'Peso da carga (kg)',
                            'Margem de segurança (%)',
                            'Peso de segurança (kg)',
                            'Peso a considerar (kg)',
                            'Peso dos cabos (3%) (kg)',
                            'Peso dos acessórios (kg)',
                            'Carga Total (kg)'
                        ],
                        'Valor': [
                            f"{resultado['peso_carga']:.2f}",
                            f"{st.session_state.dados_icamento['margem_seguranca_percentual']}",
                            f"{resultado['peso_seguranca']:.2f}",
                            f"{resultado['peso_considerar']:.2f}",
                            f"{resultado['peso_cabos']:.2f}",
                            f"{resultado['peso_acessorios']:.2f}",
                            f"{resultado['carga_total']:.2f}"
                        ]
                    })
                    st.table(df_resultados)


                    if capacidade_raio > 0 and capacidade_alcance > 0:
                        validacao = validar_guindaste(
                            resultado['carga_total'],
                            capacidade_raio,
                            capacidade_alcance,
                            raio_max, # Passar o raio para a validação, se necessário
                            alcance_max # Passar o alcance para a validação, se necessário
                        )
                        
                        st.session_state.dados_icamento['validacao'] = validacao

                        st.subheader("🎯 Resultado da Validação")
                        
                        if validacao['adequado']:
                            st.success("✅ " + validacao['mensagem'])
                        else:
                            st.error("⚠️ " + validacao['mensagem'])
                        
                        col1_metric, col2_metric = st.columns(2) # Renomeadas
                        with col1_metric:
                            st.metric(
                                "Utilização no Raio Máximo",
                                f"{validacao['detalhes']['porcentagem_raio']:.1f}%",
                                help="Percentual da capacidade utilizada no raio máximo"
                            )
                        with col2_metric:
                            st.metric(
                                "Utilização na Lança Máxima",
                                f"{validacao['detalhes']['porcentagem_alcance']:.1f}%",
                                help="Percentual da capacidade utilizada na extensão máxima"
                            )
                        
                        if validacao['detalhes']['porcentagem_raio'] > 80 or validacao['detalhes']['porcentagem_alcance'] > 80:
                             st.warning("⚠️ **Atenção:** Utilização acima de 80%. Necessária aprovação da engenharia e segurança.")


                        if raio_max > 0 and alcance_max > 0: # Condição para gerar diagrama
                            st.subheader("🏗️ Diagrama do Guindaste")
                            try:
                                fig = criar_diagrama_guindaste(
                                    raio_max, 
                                    alcance_max,
                                    resultado['carga_total'],
                                    capacidade_raio,
                                    angulo_minimo_fabricante
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                st.info(f"""
                                **Legenda do Diagrama:**
                                - **Linha Laranja**: Ângulo mínimo do fabricante ({angulo_minimo_fabricante}°)
                                - **Linha Verde Tracejada**: Posição segura da lança (considerando carga e capacidade)
                                - **Linha Azul/Vermelha**: Posição atual da lança (baseada em raio_max e alcance_max)
                                - **Área Vermelha Clara**: Zona de perigo (ângulo > 80°, sobre o guindaste)
                                
                                ⚠️ **Importante:**
                                - Mantenha a operação acima do ângulo mínimo do fabricante.
                                - Observe os limites de capacidade e as indicações de segurança.
                                - As condições reais do local e do tempo devem ser consideradas.
                                """)
                            except Exception as e:
                                st.error(f"Erro ao gerar o diagrama: {str(e)}")
                        elif raio_max == 0 or alcance_max == 0:
                            st.warning("Diagrama não gerado: Raio máximo ou Alcance máximo não podem ser zero.")


                except ValueError as e:
                    st.error(f"Erro de valor nos dados de entrada: {str(e)}")
                except KeyError as e:
                    st.error(f"Erro ao processar resultados (chave não encontrada): {str(e)}. Verifique as saídas das funções de cálculo.")
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado durante o cálculo: {str(e)}")
        
# ------------------------------------------------------------------------------------------------------------------------------

        with tab2:
            st.header("Informações e Documentos do Guindauto")
            if 'id_avaliacao' not in st.session_state: st.session_state.id_avaliacao = gerar_id_avaliacao()
            st.info(f"ID da Avaliação: **{st.session_state.id_avaliacao}**")
            
            uploader = GoogleDriveUploader()
            ai_processor = PDFQA()
            if 'uploads' not in st.session_state: st.session_state.uploads = {}

            st.subheader("📋 Dados Cadastrais")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.session_state.empresa_form = st.text_input("Empresa", value=st.session_state.empresa_form)
                st.session_state.cnpj_form = st.text_input("CNPJ", value=st.session_state.cnpj_form)
                st.session_state.operador_form = st.text_input("Nome do Operador", value=st.session_state.operador_form)
                st.session_state.cpf_form = st.text_input("CPF do Operador", value=st.session_state.cpf_form)
            with col_c2:
                st.session_state.telefone_form = st.text_input("Telefone", value=st.session_state.telefone_form)
                st.session_state.email_form = st.text_input("Email", value=st.session_state.email_form)
                st.session_state.cnh_form = st.text_input("Número da CNH", value=st.session_state.cnh_form)
                st.session_state.cnh_validade_form = st.date_input("Validade da CNH", value=st.session_state.cnh_validade_form)

            st.subheader("🏗️ Dados do Equipamento")
            crlv_file = st.file_uploader("Upload do CRLV (.pdf)", type='pdf', key="crlv_uploader")
            if crlv_file and 'crlv_extracted' not in st.session_state:
                st.session_state.uploads['crlv'] = handle_upload_with_id(uploader, crlv_file, 'crlv', st.session_state.id_avaliacao)
                extracted = ai_processor.extract_structured_data(crlv_file, get_crlv_prompt())
                if extracted:
                    st.session_state.placa_form = extracted.get('placa', st.session_state.placa_form)
                    st.session_state.ano_form = int(extracted.get('ano_fabricacao') or st.session_state.ano_form)
                    st.session_state.modelo_form = extracted.get('marca_modelo', st.session_state.modelo_form)
                    st.session_state.crlv_extracted = True
                    st.rerun()
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.session_state.placa_form = st.text_input("Placa Guindaste", value=st.session_state.placa_form)
                st.session_state.modelo_form = st.text_input("Modelo Equipamento", value=st.session_state.modelo_form)
            with col_e2:
                st.session_state.fabricante_form = st.text_input("Fabricante Equipamento", value=st.session_state.fabricante_form)
                st.session_state.ano_form = st.number_input("Ano Fabricação", min_value=1950, max_value=date.today().year + 1, value=st.session_state.ano_form)

            st.subheader("📄 Documentação e Validades")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.markdown("**ART**"); art_file = st.file_uploader("Doc. ART (.pdf)", key="art_uploader")
                if art_file and 'art_extracted' not in st.session_state:
                    st.session_state.uploads['art_doc'] = handle_upload_with_id(uploader, art_file, 'art_doc', st.session_state.id_avaliacao)
                    extracted = ai_processor.extract_structured_data(art_file, get_art_prompt())
                    if extracted:
                        st.session_state.art_num_form = extracted.get('numero_art', st.session_state.art_num_form)
                        data_emissao = extracted.get('data_emissao', '')
                        if data_emissao:
                            try:
                                st.session_state.art_validade_form = datetime.strptime(data_emissao, "%Y-%m-%d").date()
                            except Exception:
                                st.session_state.art_validade_form = data_emissao
                        st.session_state.art_extracted = True
                        st.rerun()
                st.session_state.art_num_form = st.text_input("Número ART", value=st.session_state.art_num_form)
                st.session_state.art_validade_form = st.date_input("Validade ART", value=st.session_state.art_validade_form)
            with col_d2:
                st.markdown("**Certificado NR-11**"); nr11_file = st.file_uploader("Cert. NR-11 (.pdf)", key="nr11_uploader")
                if nr11_file and 'nr11_extracted' not in st.session_state:
                    st.session_state.uploads['nr11_doc'] = handle_upload_with_id(uploader, nr11_file, 'nr11_doc', st.session_state.id_avaliacao)
                    extracted = ai_processor.extract_structured_data(nr11_file, get_nr11_prompt())
                    if extracted:
                        st.session_state.operador_form = extracted.get('nome_operador', st.session_state.operador_form)
                        st.session_state.nr11_num_form = extracted.get('numero_nr11', getattr(st.session_state, 'nr11_num_form', ''))
                        data_emissao = extracted.get('data_emissao', '')
                        if data_emissao:
                            try:
                                st.session_state.nr11_data_form = datetime.strptime(data_emissao, "%Y-%m-%d").date()
                            except Exception:
                                st.session_state.nr11_data_form = data_emissao
                        validade = extracted.get('validade', '')
                        if validade:
                            try:
                                st.session_state.nr11_validade_form = datetime.strptime(validade, "%Y-%m-%d").date()
                            except Exception:
                                st.session_state.nr11_validade_form = validade
                        st.session_state.nr11_extracted = True
                        st.rerun()
                st.session_state.nr11_num_form = st.text_input("Número NR-11", value=getattr(st.session_state, 'nr11_num_form', ''))
                st.session_state.nr11_data_form = st.date_input("Emissão NR-11", value=st.session_state.nr11_data_form)
                if hasattr(st.session_state, 'nr11_validade_form') and st.session_state.nr11_validade_form:
                    if st.session_state.nr11_validade_form >= date.today():
                        st.success(f"Válido até: {st.session_state.nr11_validade_form.strftime('%d/%m/%Y')}")
                    else:
                        st.error(f"Vencido em: {st.session_state.nr11_validade_form.strftime('%d/%m/%Y')}")
                elif st.session_state.nr11_data_form:
                    validade = st.session_state.nr11_data_form + relativedelta(years=1)
                    if validade >= date.today(): st.success(f"Válido até: {validade.strftime('%d/%m/%Y')}")
                    else: st.error(f"Vencido em: {validade.strftime('%d/%m/%Y')}")
            with col_d3:
                st.markdown("**Manutenção (M_PREV)**"); mprev_file = st.file_uploader("Doc. M_PREV (.pdf)", key="mprev_uploader")
                if mprev_file: st.session_state.uploads['mprev_doc'] = handle_upload_with_id(uploader, mprev_file, 'mprev_doc', st.session_state.id_avaliacao)
                st.session_state.mprev_data_form = st.date_input("Data Última Manut.", value=st.session_state.mprev_data_form)
                if st.session_state.mprev_data_form:
                    st.session_state.mprev_prox_form = st.session_state.mprev_data_form + relativedelta(years=1)
                    if st.session_state.mprev_prox_form >= date.today(): st.success(f"Próxima até: {st.session_state.mprev_prox_form.strftime('%d/%m/%Y')}")
                    else: st.error(f"Vencida desde: {st.session_state.mprev_prox_form.strftime('%d/%m/%Y')}")

            st.subheader("Arquivos Adicionais")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                cnh_doc_file = st.file_uploader("Upload da CNH (.pdf, .png)", key="cnh_doc_uploader")
                if cnh_doc_file and 'cnh_extracted' not in st.session_state:
                    st.session_state.uploads['cnh_doc'] = handle_upload_with_id(uploader, cnh_doc_file, 'cnh_doc', st.session_state.id_avaliacao)
                    extracted = ai_processor.extract_structured_data(cnh_doc_file, get_cnh_prompt())
                    if extracted:
                        st.session_state.operador_form = extracted.get('nome', st.session_state.operador_form)
                        st.session_state.cnh_form = extracted.get('numero_cnh', st.session_state.cnh_form)
                        validade = extracted.get('validade', '')
                        if validade:
                            try:
                                st.session_state.cnh_validade_form = datetime.strptime(validade, "%Y-%m-%d").date()
                            except Exception:
                                st.session_state.cnh_validade_form = validade
                        st.session_state.cpf_form = extracted.get('cpf', st.session_state.cpf_form)
                        st.session_state.cnh_extracted = True
                        st.rerun()
            with col_a2:
                grafico_carga_file = st.file_uploader("Gráfico de Carga (.pdf, .png)", key="grafico_uploader");
                if grafico_carga_file: st.session_state.uploads['grafico_doc'] = handle_upload_with_id(uploader, grafico_carga_file, 'grafico_doc', st.session_state.id_avaliacao)

            st.session_state.obs_form = st.text_area("Observações Adicionais", value=st.session_state.obs_form)

            st.divider()
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("💾 Salvar Todas as Informações", type="primary", use_container_width=True):
                    if 'dados_icamento' not in st.session_state:
                        st.error("Calcule os dados de içamento na Aba 1 primeiro.")
                    else:
                        id_avaliacao = st.session_state.id_avaliacao
                        uploads = st.session_state.get('uploads', {})
                        get_url = lambda key: uploads.get(key, {}).get('url', '') if uploads.get(key) else ''
                        
                        dados_guindauto_row = [
                            id_avaliacao, st.session_state.empresa_form, st.session_state.cnpj_form, st.session_state.telefone_form,
                            st.session_state.email_form, st.session_state.operador_form, st.session_state.cpf_form, st.session_state.cnh_form,
                            st.session_state.cnh_validade_form.isoformat() if st.session_state.cnh_validade_form else '',
                            "NR-11", st.session_state.placa_form, st.session_state.modelo_form, st.session_state.fabricante_form,
                            st.session_state.ano_form, st.session_state.mprev_data_form.isoformat() if st.session_state.mprev_data_form else '',
                            st.session_state.mprev_prox_form.isoformat() if st.session_state.mprev_prox_form else '',
                            st.session_state.art_num_form, st.session_state.art_validade_form.isoformat() if st.session_state.art_validade_form else '',
                            st.session_state.obs_form,
                            get_url('art_doc'), get_url('nr11_doc'), get_url('cnh_doc'), get_url('crlv'), get_url('mprev_doc')
                        ]
                        # Construir linha da Tab 1 para salvar
                        d_icamento = st.session_state.dados_icamento
                        v_icamento = d_icamento.get('validacao', {})
                        det_icamento = v_icamento.get('detalhes', {})
                        dados_icamento_row = [id_avaliacao, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), d_icamento.get('peso_carga'), d_icamento.get('margem_seguranca_percentual'), d_icamento.get('peso_seguranca'), d_icamento.get('peso_cabos'), d_icamento.get('peso_acessorios'), d_icamento.get('carga_total'), v_icamento.get('adequado'), f"{det_icamento.get('porcentagem_raio', 0):.1f}%", f"{det_icamento.get('porcentagem_alcance', 0):.1f}%", d_icamento.get('fabricante_guindaste'), d_icamento.get('modelo_guindaste'), d_icamento.get('raio_max'), d_icamento.get('capacidade_raio'), d_icamento.get('alcance_max'), d_icamento.get('capacidade_alcance'), d_icamento.get('angulo_minimo_fabricante')]

                        try:
                            with st.spinner("Salvando..."):
                                uploader.append_data_to_sheet(LIFTING_SHEET_NAME, dados_icamento_row)
                                uploader.append_data_to_sheet(CRANE_SHEET_NAME, dados_guindauto_row)
                            st.success(f"✅ Operação registrada com ID: {id_avaliacao}"); st.balloons()
                            keys_to_clear = [k for k in st.session_state.keys() if 'form' in k or 'upload' in k or 'id_avaliacao' in k or 'dados_icamento' in k]
                            for key in keys_to_clear: del st.session_state[key]
                            time.sleep(3); st.rerun()
                        except Exception as e: st.error(f"Erro ao salvar: {e}")
            with col_s2:
                if st.button("🔄 Limpar Formulário", use_container_width=True):
                    keys_to_clear = [k for k in st.session_state.keys() if 'form' in k or 'upload' in k or 'id_avaliacao' in k or 'dados_icamento' in k]
                    for key in keys_to_clear: del st.session_state[key]
                    st.warning("⚠️ Formulário limpo."); st.rerun()
    
