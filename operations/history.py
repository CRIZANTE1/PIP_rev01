import streamlit as st
import pandas as pd
from datetime import datetime
from gdrive.gdrive_upload import GoogleDriveUploader
from gdrive.config import LIFTING_SHEET_NAME, CRANE_SHEET_NAME
from operations.plot import criar_diagrama_guindaste
from operations.report_generator import generate_abnt_report

@st.cache_data(ttl=600)
def load_sheet_data(sheet_name):
    """Carrega dados de uma aba específica do Google Sheets."""
    try:
        uploader = GoogleDriveUploader()
        data = uploader.get_data_from_sheet(sheet_name)
        if not data or len(data) < 2: 
            st.warning(f"A planilha '{sheet_name}' está vazia ou não foi encontrada.")
            return pd.DataFrame()
        headers, rows = data[0], data[1:]
        max_cols = len(headers)
        cleaned_rows = [row[:max_cols] + [None] * (max_cols - len(row)) for row in rows]
        return pd.DataFrame(cleaned_rows, columns=headers)
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha '{sheet_name}': {e}")
        return pd.DataFrame()

# CORREÇÃO: A função make_urls_clickable não é mais necessária e foi removida.

def get_status_from_date(date_str):
    """Calcula o status (Válido/Vencido) a partir de uma string de data."""
    if not date_str or not isinstance(date_str, str): return "Status Indeterminado"
    today = datetime.now().date()
    try:
        expiry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            expiry_date = datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return "Data em formato inválido"
    return "Válido" if expiry_date >= today else "Vencido"

def render_document_status(dados_guindauto):
    """Renderiza a lista de documentos calculando o status em tempo real."""
    st.subheader("Documentos Avaliados")
    doc_map = {
        "ART (Anot. Resp. Técnica)": {"url_col": "URL ART", "date_col": "Validade ART"},
        "Certificação NR-11":        {"url_col": "URL Certificado", "date_col": None},
        "CNH do Operador":           {"url_col": "URL CNH", "date_col": "Validade CNH"},
        "Manutenção Preventiva":     {"url_col": "URL M_PREV", "date_col": "Próxima Manutenção"},
        "CRLV do Veículo":           {"url_col": "URL CRLV", "date_col": None},
        "Gráfico de Carga":          {"url_col": "URL Gráfico de Carga", "date_col": None}
    }
    for doc_name, cols in doc_map.items():
        url = dados_guindauto.get(cols["url_col"])
        if pd.notna(url) and str(url).strip().startswith('http'):
            link = f"<a href='{url}' target='_blank'>Abrir Documento</a>"
            if cols["date_col"]:
                date_value = dados_guindauto.get(cols["date_col"])
                status = get_status_from_date(date_value)
                if "Válido" in status:
                    st.markdown(f"✅ **{doc_name}**: {status} - {link}", unsafe_allow_html=True)
                else:
                    st.markdown(f"❌ **{doc_name}**: {status} - {link}", unsafe_allow_html=True)
            else:
                st.markdown(f"✅ **{doc_name}**: {link}", unsafe_allow_html=True)
        else:
            st.markdown(f"❌ **{doc_name}**: Documento não fornecido")

def safe_to_numeric(series):
    """Converte uma série para numérico de forma segura, tratando vírgulas."""
    if series is None: return None
    return pd.to_numeric(str(series).replace(',', '.'), errors='coerce')

def render_diagrama(dados_icamento):
    """Adota um valor padrão de 40 graus para o ângulo mínimo se não for encontrado."""
    st.subheader("Diagrama da Operação")
    try:
        raio_max = safe_to_numeric(dados_icamento.get('Raio Máximo (m)'))
        alcance_max = safe_to_numeric(dados_icamento.get('Alcance Máximo (m)'))
        carga_total = safe_to_numeric(dados_icamento.get('Carga Total (kg)'))
        capacidade_raio = safe_to_numeric(dados_icamento.get('Capacidade Raio (kg)'))
        angulo_minimo = safe_to_numeric(dados_icamento.get('Ângulo Mínimo da Lança'))
        if pd.isna(angulo_minimo):
            angulo_minimo = 40.0
            st.info("Ângulo mínimo da lança não informado. Adotando 40° como padrão para o diagrama.")
        if all(pd.notna([raio_max, alcance_max, carga_total, capacidade_raio])):
            fig = criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não foi possível gerar o diagrama. Verifique se os campos de Raio, Alcance e Capacidades estão preenchidos no registro.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao renderizar o diagrama: {e}")

def show_history_page():
    st.title("Histórico de Avaliações")
    st.info("Os dados são atualizados a cada 10 minutos. Para forçar a atualização, limpe o cache.")
    if st.button("Limpar Cache e Recarregar Dados"):
        st.cache_data.clear()
        st.rerun()
    with st.spinner("Carregando dados das planilhas..."):
        df_lifting = load_sheet_data(LIFTING_SHEET_NAME)
        df_crane = load_sheet_data(CRANE_SHEET_NAME)
    if df_lifting.empty or df_crane.empty:
        st.warning("Não foi possível carregar os dados do histórico. Verifique se ambas as planilhas estão preenchidas.")
        return

    st.subheader("Buscar e Analisar Avaliação por ID")
    # ... (o bloco de busca por ID permanece o mesmo)
    id_column = df_lifting.columns[0]
    search_id = st.text_input("Digite o ID da Avaliação (ex: AV20240101-abcdefgh)", key="search_id_input")
    if st.button("Buscar por ID", key="search_button") and search_id:
        st.markdown("---")
        result_lifting = df_lifting[df_lifting[id_column] == search_id]
        result_crane = df_crane[df_crane.iloc[:, 0] == search_id]
        if not result_lifting.empty and not result_crane.empty:
            dados_icamento = result_lifting.iloc[0]
            dados_guindauto = result_crane.iloc[0]
            
            st.markdown("---")
            with st.spinner("Gerando relatório PDF..."):
                pdf_report = generate_abnt_report(dados_icamento, dados_guindauto)
                st.download_button(
                    label="📄 Baixar Relatório ABNT (PDF)",
                    data=pdf_report,
                    file_name=f"Relatorio_Içamento_{search_id}.pdf",
                    mime="application/pdf"
                )
            st.markdown("---")

            st.header(f"Análise Detalhada da Avaliação: {search_id}")
            col1, col2 = st.columns([2, 1])
            with col1:
                render_diagrama(dados_icamento)
            with col2:
                st.subheader("Principais Indicadores")
                carga_total_val = safe_to_numeric(dados_icamento.get('Carga Total (kg)', 0))
                st.metric("Carga Total da Operação", f"{carga_total_val:,.2f} kg".replace(",", "."))
                st.metric("Utilização no Raio", dados_icamento.get('% Utilização Raio', 'N/A'))
                st.metric("Utilização na Lança", dados_icamento.get('% Utilização Alcance', 'N/A'))
                adequado = dados_icamento.get('Adequado')
                if str(adequado).strip().upper() == 'TRUE':
                    st.success("✅ Operação Aprovada")
                else:
                    st.error("❌ Operação Reprovada")
                st.markdown("---")
                st.write(f"**Operador:** {dados_guindauto.get('Nome Operador', 'N/A')}")
                st.write(f"**Veículo (Placa):** {dados_guindauto.get('Placa Guindaste', 'N/A')}")
            st.markdown("---")
            render_document_status(dados_guindauto)
            with st.expander("Ver todos os dados brutos desta avaliação"):
                st.subheader("Dados de Içamento")
                st.dataframe(result_lifting.T, use_container_width=True)
                st.subheader("Informações do Guindauto")
                st.dataframe(result_crane.set_index(result_crane.columns[0]).T, use_container_width=True) # Exibição transposta melhorada
        else:
            st.warning(f"Nenhum registro completo encontrado para o ID: {search_id}.")

    st.markdown("---")
    st.subheader("Histórico Completo (Visão Geral)")
    
    tab1, tab2 = st.tabs(["Dados de Içamento", "Informações do Guindauto"])

    with tab1:
        if not df_lifting.empty:
            st.dataframe(df_lifting, use_container_width=True)
        else:
            st.info("Nenhum histórico de dados de içamento encontrado.")

    with tab2:
        if not df_crane.empty:
            
            column_config = {}
            for col_name in df_crane.columns:
                if "URL" in col_name.upper():
                    column_config[col_name] = st.column_config.LinkColumn(
                        "Link do Documento",
                        display_text="Abrir ↗"  
                    )
            
            st.dataframe(
                df_crane,
                use_container_width=True,
                column_config=column_config,
                hide_index=True,
            )
        else:
            st.info("Nenhum histórico de informações de guindauto encontrado.")




