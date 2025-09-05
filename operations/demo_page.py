import streamlit as st
import pandas as pd
from operations.calc import calcular_carga_total, validar_guindaste
from operations.plot import criar_diagrama_guindaste

def show_demo_page():
    """
    Exibe uma página de demonstração INTERATIVA com a calculadora de içamento.
    """
    st.title("Calculadora de Movimentação de Carga")
    st.warning("🔒 Versão de Demonstração Interativa", icon="🧪")
    st.markdown("""
    Você está em um ambiente de demonstração. Use a calculadora abaixo para testar a funcionalidade de análise de içamento. 
    **Nenhum dado será salvo.** Para acesso completo, incluindo upload de documentos e histórico, por favor, entre em contato com o administrador.
    """)
    st.divider()


    demo_keys = [
        "demo_estado_equip_radio", "demo_peso_carga", "demo_peso_acessorios",
        "demo_fabricante_guindaste_calc", "demo_nome_guindaste_calc", "demo_raio_max",
        "demo_capacidade_raio", "demo_extensao_lanca", "demo_capacidade_alcance",
        "demo_angulo_minimo_input"
    ]
    for key in demo_keys:
        if key not in st.session_state:
            st.session_state[key] = 0.0 if "peso" in key or "raio" in key or "capacidade" in key or "extensao" in key else ""
            if key == "demo_estado_equip_radio": st.session_state[key] = "Novo"
            if key == "demo_angulo_minimo_input": st.session_state[key] = 40.0


    # --- Layout da Calculadora ---
    st.header("Análise e Simulação de Içamento")
    col_inputs, col_results = st.columns([1, 2], gap="large")
    
    with col_inputs:
        st.subheader("Parâmetros da Operação")
        
        st.radio(
            "Estado do Equipamento", ["Novo", "Usado"], key="demo_estado_equip_radio",
            help="Novo: 10% de margem. Usado: 25%."
        )
        if st.session_state.demo_estado_equip_radio == "Novo":
            st.info("Margem de segurança de 10% aplicada.")
        else:
            st.warning("⚠️ Margem de segurança de 25% aplicada para equipamento usado.")

        st.number_input("Peso da carga (kg)", min_value=0.0, step=100.0, key="demo_peso_carga")
        st.number_input("Peso dos acessórios (kg)", min_value=0.0, step=1.0, key="demo_peso_acessorios")
        st.divider()
        st.text_input("Fabricante do Guindaste", key="demo_fabricante_guindaste_calc")
        st.text_input("Nome do Guindaste", key="demo_nome_guindaste_calc", placeholder="Ex: AGI, XCA250 BR II")
        st.number_input("Raio de Operação (m)", min_value=0.0, step=0.1, key="demo_raio_max")
        st.number_input("Capacidade no Raio (kg)", min_value=0.0, step=100.0, key="demo_capacidade_raio")
        st.number_input("Extensão da Lança (m)", min_value=0.0, step=0.1, key="demo_extensao_lanca")
        st.number_input("Capacidade na Lança (kg)", min_value=0.0, step=100.0, key="demo_capacidade_alcance")
        st.number_input(
            "Ângulo Mínimo da Lança (°)", min_value=1.0, max_value=89.0,
            key="demo_angulo_minimo_input"
        )

    with col_results:
        st.subheader("Resultados e Análise em Tempo Real")
        
        inputs_validos = all([
            st.session_state.demo_peso_carga > 0, st.session_state.demo_raio_max > 0,
            st.session_state.demo_capacidade_raio > 0, st.session_state.demo_extensao_lanca > 0,
            st.session_state.demo_capacidade_alcance > 0
        ])

        if not inputs_validos:
            st.info("📊 Preencha todos os parâmetros à esquerda para ver os resultados e o diagrama.")
        else:
            try:
                equip_novo = st.session_state.demo_estado_equip_radio == "Novo"
                resultado_calc = calcular_carga_total(st.session_state.demo_peso_carga, equip_novo, st.session_state.demo_peso_acessorios)
                
                validacao = validar_guindaste(
                    carga_total=resultado_calc['carga_total'], 
                    capacidade_raio=st.session_state.demo_capacidade_raio, 
                    capacidade_alcance_max=st.session_state.demo_capacidade_alcance, 
                    raio_max=st.session_state.demo_raio_max, 
                    extensao_lanca=st.session_state.demo_extensao_lanca,
                    angulo_minimo_fabricante=st.session_state.demo_angulo_minimo_input
                )

                mensagem_validacao = validacao.get('mensagem', 'Falha na validação.')
                if "INSEGURA" in mensagem_validacao.upper():
                    st.error(f"❌ {mensagem_validacao}")
                elif "ATENÇÃO" in mensagem_validacao.upper():
                    st.warning(f"⚠️ {mensagem_validacao}")
                else:
                    st.success(f"✅ {mensagem_validacao}")
                
                st.plotly_chart(
                    criar_diagrama_guindaste(
                        st.session_state.demo_raio_max, st.session_state.demo_extensao_lanca, 
                        resultado_calc['carga_total'], st.session_state.demo_capacidade_raio, 
                        st.session_state.demo_angulo_minimo_input
                    ), 
                    use_container_width=True
                )

                col_tabela, col_metricas = st.columns(2)
                with col_tabela:
                    st.dataframe(pd.DataFrame({
                        'Descrição': ['Peso Carga', 'Margem (%)', 'Peso Segurança', 'Peso Acessórios', 'Peso Cabos (3%)', 'CARGA TOTAL'],
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
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
