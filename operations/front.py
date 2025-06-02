import streamlit as st
from operations.calc import calcular_carga_total, validar_guindaste
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
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
    # Inicialização das variáveis para evitar erros de "não definido"
    empresa_responsavel = "" # Renomeado para evitar conflito com 'fabricante'
    cnpj = ""
    telefone = ""
    email = ""
    nome_operador = ""
    cpf_operador = ""
    cnh = ""
    validade_cnh = None # datetime.date object or None
    certificacoes = []
    placa_equip = "" # Renomeado para clareza
    modelo_equip = ""
    fabricante_equip = "" # Renomeado para clareza
    ano_equip = datetime.now().year # Default to current year
    ultima_manutencao = None # datetime.date object or None
    proxima_manutencao = None # datetime.date object or None
    num_art = ""
    validade_art = None # datetime.date object or None
    observacoes = ""

    st.title("Calculadora de Carga")
    
 
    mostrar_instrucoes()
    
   
    tab1, tab2 = st.tabs(["📝 Dados do Içamento", "🏗️ Informações do Guindauto"])

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
        st.header("Informações Complementares")
        
        if 'id_avaliacao' not in st.session_state:
            st.session_state.id_avaliacao = gerar_id_avaliacao()
        
        st.info(f"ID da Avaliação: {st.session_state.id_avaliacao}")
        
        uploader = GoogleDriveUploader() # Inicializar uma vez por aba ou sessão, se possível
        
        st.subheader("📊 Gráfico de Carga do Fabricante")
        
        grafico_carga = st.file_uploader(
            "Upload do Gráfico de Carga (.png, .jpg, .jpeg)",
            type=['png', 'jpg', 'jpeg'],
            key="grafico_carga_uploader",
            help="Faça upload da imagem do gráfico de carga do fabricante"
        )
        
        if grafico_carga is not None:
            st.image(
                grafico_carga,
                caption="Gráfico de Carga do Fabricante",
                use_container_width=True
            )
            if 'uploads' not in st.session_state:
                st.session_state.uploads = {}

            # Evitar re-upload na mesma sessão se já existir e o arquivo for o mesmo (opcional, mas bom para UX)
            # Para simplificar, vamos permitir o re-upload se o usuário selecionar um novo arquivo.
            
            # Upload sempre que um arquivo é fornecido e o botão de salvar for pressionado (ou automaticamente)
            # No modelo atual, o upload é feito aqui mesmo, o que pode ser repetitivo se não for salvo.
            # Considerar mover o upload para o botão "Salvar Informações"
            
            # Para este exemplo, vamos manter o upload imediato após seleção.
            if 'grafico_uploaded_name' not in st.session_state or st.session_state.grafico_uploaded_name != grafico_carga.name:
                resultado_upload = handle_upload_with_id(
                    uploader, 
                    grafico_carga, 
                    'grafico', 
                    st.session_state.id_avaliacao
                )
                if resultado_upload and resultado_upload['success']:
                    st.success(f"✅ Arquivo '{resultado_upload['nome']}' pronto para ser associado ao ID {st.session_state.id_avaliacao}.")
                    st.markdown(f"Link temporário (será salvo com o formulário): {resultado_upload['url']}")
                    st.session_state.uploads['grafico'] = resultado_upload
                    st.session_state.grafico_uploaded_name = grafico_carga.name # Para evitar re-upload se o arquivo não mudar
                elif resultado_upload:
                    st.error(f"Erro no upload do gráfico: {resultado_upload['error']}")


        st.info("""
        **Instruções para o Gráfico de Carga:**
        1. Deve ser a imagem oficial do manual do fabricante, legível e completa.
        2. Formatos: PNG, JPG/JPEG.
        3. Certifique-se que as informações estão atualizadas e correspondem ao modelo.
        """)

        st.subheader("📋 Dados da Empresa")
        col1_emp, col2_emp = st.columns(2)
        with col1_emp:
            empresa_responsavel = st.text_input(
                "Nome da Empresa Responsável",
                value=st.session_state.get('empresa_responsavel_form', ''),
                help=" Nome da empresa responsável pela operação"
            )
            cnpj = st.text_input(
                "CNPJ",
                value=st.session_state.get('cnpj_form', ''),
                help=" CNPJ da empresa (formato: XX.XXX.XXX/XXXX-XX)"
            )
            
        with col2_emp:
            telefone = st.text_input("Telefone", value=st.session_state.get('telefone_form', ''))
            email = st.text_input("E-mail", value=st.session_state.get('email_form', ''))

        st.subheader("👤 Dados do Operador")
        col1_op, col2_op, col3_op = st.columns(3)
        with col1_op:
            nome_operador = st.text_input(
                "Nome do Operador",
                value=st.session_state.get('nome_operador_form', ''),
                help="Nome completo do operador certificado do guindaste"
            )
            cpf_operador = st.text_input("CPF do Operador", value=st.session_state.get('cpf_operador_form', ''))
        
        with col2_op:
            cnh = st.text_input("CNH", value=st.session_state.get('cnh_form', ''))
            validade_cnh_input = st.date_input(
                "Validade CNH", 
                value=st.session_state.get('validade_cnh_form', None),
                min_value=datetime.today().date() # Opcional: CNH não pode estar vencida
            )
        
        with col3_op:
            certificacoes_input = st.multiselect(
                "Certificações do Operador",
                ["NR-11", "NR-12", "NR-18", "NR-35", "Outro"],
                default=st.session_state.get('certificacoes_form', []),
                help=" Normas regulamentadoras que o operador possui certificação"
            )

        st.subheader("🏗️ Dados do Equipamento (Guindauto)")
        col1_equip, col2_equip = st.columns(2)
        with col1_equip:
            placa_equip = st.text_input("Placa do Guindauto", value=st.session_state.get('placa_equip_form', ''))
            modelo_equip = st.text_input("Modelo do Equipamento", value=st.session_state.get('modelo_equip_form', ''))
            fabricante_equip = st.text_input("Fabricante do Equipamento", value=st.session_state.get('fabricante_equip_form', ''))
        
        with col2_equip:
            ano_equip_input = st.number_input("Ano de Fabricação", min_value=1950, max_value=datetime.now().year + 1, value=st.session_state.get('ano_equip_form', datetime.now().year), step=1)
            ultima_manutencao_input = st.date_input("Data Última Manutenção", value=st.session_state.get('ultima_manutencao_form', None))
            proxima_manutencao_input = st.date_input("Data Próxima Manutenção", value=st.session_state.get('proxima_manutencao_form', None))

       
        st.subheader("📄 Documentação Adicional")
        col1_doc, col2_doc = st.columns(2)
        with col1_doc:
            num_art = st.text_input(
                "Número da ART",
                value=st.session_state.get('num_art_form', ''),
                help="Número da Anotação de Responsabilidade Técnica do engenheiro responsável"
            )
            validade_art_input = st.date_input("Validade da ART", value=st.session_state.get('validade_art_form', None))
            
            art_file = st.file_uploader("Upload da ART (.pdf)", type=['pdf'], key="art_uploader")
            if art_file:
                if 'uploads' not in st.session_state: st.session_state.uploads = {}
                if 'art_uploaded_name' not in st.session_state or st.session_state.art_uploaded_name != art_file.name:
                    resultado_art = handle_upload_with_id(uploader, art_file, 'art', st.session_state.id_avaliacao)
                    if resultado_art and resultado_art['success']:
                        st.success(f"✅ ART '{resultado_art['nome']}' pronta para ser associada.")
                        st.markdown(f"Link temporário: {resultado_art['url']}")
                        st.session_state.uploads['art'] = resultado_art
                        st.session_state.art_uploaded_name = art_file.name
                    elif resultado_art:
                        st.error(f"Erro no upload da ART: {resultado_art['error']}")
        
        with col2_doc:
            cert_file = st.file_uploader("Certificado de Calibração (.pdf)", type=['pdf'], key="cert_calibracao_uploader")
            if cert_file:
                if 'uploads' not in st.session_state: st.session_state.uploads = {}
                if 'cert_uploaded_name' not in st.session_state or st.session_state.cert_uploaded_name != cert_file.name:
                    resultado_cert = handle_upload_with_id(uploader, cert_file, 'cert', st.session_state.id_avaliacao)
                    if resultado_cert and resultado_cert['success']:
                        st.success(f"✅ Certificado '{resultado_cert['nome']}' pronto para ser associado.")
                        st.markdown(f"Link temporário: {resultado_cert['url']}")
                        st.session_state.uploads['cert'] = resultado_cert
                        st.session_state.cert_uploaded_name = cert_file.name
                    elif resultado_cert:
                        st.error(f"Erro no upload do Certificado: {resultado_cert['error']}")
        
        st.text_area("Observações Adicionais", value=st.session_state.get('observacoes_form', ''), key="observacoes_text_area")
        
        col1_save, col2_clear = st.columns(2)
        with col1_save:
            if st.button("💾 Salvar Informações no Google Drive"):
                if 'id_avaliacao' not in st.session_state:
                    st.error("Erro: ID da avaliação não gerado. Por favor, recarregue a página.")
                else:
                    id_avaliacao = st.session_state.id_avaliacao
                    
                    dados_icamento = st.session_state.get('dados_icamento', {})
                    if not dados_icamento:
                        st.error("Dados do içamento (Tab 1) não calculados. Por favor, calcule-os primeiro.")
                        return # Use return para sair da função do botão

                    uploads = st.session_state.get('uploads', {})
                    url_grafico = uploads.get('grafico', {}).get('url', '')
                    url_art = uploads.get('art', {}).get('url', '')
                    url_cert = uploads.get('cert', {}).get('url', '')

                    dados_icamento_row = [
                        id_avaliacao,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        dados_icamento.get('peso_carga', ''),
                        dados_icamento.get('margem_seguranca_percentual', ''),
                        dados_icamento.get('peso_seguranca', ''),
                        dados_icamento.get('peso_cabos', ''),
                        dados_icamento.get('peso_acessorios', ''),
                        dados_icamento.get('carga_total', ''),
                        dados_icamento.get('validacao', {}).get('adequado', ''),
                        f"{dados_icamento.get('validacao', {}).get('detalhes', {}).get('porcentagem_raio', ''):.1f}" if isinstance(dados_icamento.get('validacao', {}).get('detalhes', {}).get('porcentagem_raio', ''), float) else '',
                        f"{dados_icamento.get('validacao', {}).get('detalhes', {}).get('porcentagem_alcance', ''):.1f}" if isinstance(dados_icamento.get('validacao', {}).get('detalhes', {}).get('porcentagem_alcance', ''), float) else '',
                        dados_icamento.get('fabricante_guindaste', ''),
                        dados_icamento.get('modelo_guindaste', ''),
                        dados_icamento.get('raio_max', ''),
                        dados_icamento.get('capacidade_raio', ''),
                        dados_icamento.get('alcance_max', ''),
                        dados_icamento.get('capacidade_alcance', ''),
                        dados_icamento.get('angulo_minimo_fabricante', '')
                    ]
                    
                    # Coletar valores dos inputs da Tab2 para salvar
                    st.session_state.empresa_responsavel_form = empresa_responsavel
                    st.session_state.cnpj_form = cnpj
                    st.session_state.telefone_form = telefone
                    st.session_state.email_form = email
                    st.session_state.nome_operador_form = nome_operador
                    st.session_state.cpf_operador_form = cpf_operador
                    st.session_state.cnh_form = cnh
                    st.session_state.validade_cnh_form = validade_cnh_input
                    st.session_state.certificacoes_form = certificacoes_input
                    st.session_state.placa_equip_form = placa_equip
                    st.session_state.modelo_equip_form = modelo_equip
                    st.session_state.fabricante_equip_form = fabricante_equip
                    st.session_state.ano_equip_form = ano_equip_input
                    st.session_state.ultima_manutencao_form = ultima_manutencao_input
                    st.session_state.proxima_manutencao_form = proxima_manutencao_input
                    st.session_state.num_art_form = num_art
                    st.session_state.validade_art_form = validade_art_input
                    st.session_state.observacoes_form = st.session_state.get('observacoes_text_area', '')


                    dados_guindauto_row = [
                        id_avaliacao,
                        st.session_state.empresa_responsavel_form,
                        st.session_state.cnpj_form,
                        st.session_state.telefone_form,
                        st.session_state.email_form,
                        st.session_state.nome_operador_form,
                        st.session_state.cpf_operador_form,
                        st.session_state.cnh_form,
                        st.session_state.validade_cnh_form.isoformat() if st.session_state.validade_cnh_form else '',
                        ", ".join(st.session_state.certificacoes_form),
                        st.session_state.placa_equip_form,
                        st.session_state.modelo_equip_form,
                        st.session_state.fabricante_equip_form,
                        st.session_state.ano_equip_form,
                        st.session_state.ultima_manutencao_form.isoformat() if st.session_state.ultima_manutencao_form else '',
                        st.session_state.proxima_manutencao_form.isoformat() if st.session_state.proxima_manutencao_form else '',
                        st.session_state.num_art_form,
                        st.session_state.validade_art_form.isoformat() if st.session_state.validade_art_form else '',
                        st.session_state.observacoes_form,
                        url_grafico,
                        url_art,
                        url_cert
                    ]
                
                    try:
                        # Uploader já foi inicializado no início da Tab2
                        uploader.append_data_to_sheet(LIFTING_SHEET_NAME, dados_icamento_row)
                        st.success(f"✅ Dados de Içamento salvos na planilha '{LIFTING_SHEET_NAME}' com ID: {id_avaliacao}")
                        
                        uploader.append_data_to_sheet(CRANE_SHEET_NAME, dados_guindauto_row)
                        st.success(f"✅ Informações do Guindauto salvas na planilha '{CRANE_SHEET_NAME}' com ID: {id_avaliacao}")
                        
                        # Limpar ID e uploads para a próxima avaliação após salvar
                        keys_to_clear_after_save = ['id_avaliacao', 'uploads', 'dados_icamento', 
                                                    'grafico_uploaded_name', 'art_uploaded_name', 'cert_uploaded_name']
                        # Também limpar os valores dos campos do formulário da tab2
                        form_keys = [k for k in st.session_state if k.endswith('_form') or k.endswith('_uploader') or k.startswith('observacoes')]
                        keys_to_clear_after_save.extend(form_keys)

                        for key in keys_to_clear_after_save:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.info("Formulário pronto para uma nova avaliação. ID e uploads foram resetados.")
                        st.rerun() # Forçar recarregamento para limpar campos e gerar novo ID visualmente

                    except Exception as e:
                        st.error(f"Erro ao salvar dados no Google Sheets: {str(e)}")
        
        with col2_clear:
            if st.button("🔄 Limpar Formulário Atual"):
                keys_to_clear = ['id_avaliacao', 'uploads', 'dados_icamento', 
                                 'grafico_uploaded_name', 'art_uploaded_name', 'cert_uploaded_name']
                form_keys = [k for k in st.session_state if k.endswith('_form') or k.endswith('_uploader') or k.startswith('observacoes')]
                keys_to_clear.extend(form_keys)
                
                # Campos da Tab1 também podem ser resetados se desejado, ou mantidos
                # Ex: st.session_state.peso_carga = 0 (se usar st.session_state para inputs da Tab1)

                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.warning("⚠️ Formulário limpo! Alguns campos podem precisar de recarregamento da página para resetar completamente.")
    