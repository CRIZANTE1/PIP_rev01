from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import pandas as pd
from datetime import datetime
import base64
import io
from pathlib import Path

from operations.plot import criar_diagrama_guindaste

def safe_to_numeric(series):
    """Converte uma série para numérico de forma segura, tratando vírgulas."""
    if series is None: return None
    return pd.to_numeric(str(series).replace(',', '.'), errors='coerce')

def generate_abnt_report(dados_icamento, dados_guindauto):
    """
    Gera um relatório PDF em formato ABNT a partir dos dados da operação.
    """
    # 1. Preparar o ambiente do Jinja2
    template_path = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template("report_template.html")

    # 2. Gerar a imagem do diagrama em memória
    raio_max = safe_to_numeric(dados_icamento.get('Raio Máximo (m)'))
    alcance_max = safe_to_numeric(dados_icamento.get('Alcance Máximo (m)'))
    carga_total = safe_to_numeric(dados_icamento.get('Carga Total (kg)'))
    capacidade_raio = safe_to_numeric(dados_icamento.get('Capacidade Raio (kg)'))
    angulo_minimo = safe_to_numeric(dados_icamento.get('Ângulo Mínimo da Lança'))
    if pd.isna(angulo_minimo):
        angulo_minimo = 40.0
        
    fig = criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo)
    
    # Exportar para bytes e converter para base64
    img_bytes = fig.to_image(format="png", scale=2) # Aumentar escala para melhor resolução
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    diagrama_base64_url = f"data:image/png;base64,{img_base64}"

    # 3. Montar o contexto com todos os dados para o template
    context = {
        "empresa_contratante": dados_guindauto.get('Empresa', 'NOME DA SUA EMPRESA'),
        "id_avaliacao": dados_icamento.name, # .name pega o índice (ID da avaliação)
        "cidade": "Sua Cidade", # Você pode adicionar isso como um campo no formulário
        "data_emissao": datetime.now().strftime("%d de %B de %Y"),
        "dados_icamento": dados_icamento,
        "dados_guindauto": dados_guindauto,
        "diagrama_base64": diagrama_base64_url
    }
    
    # 4. Renderizar o HTML com os dados
    html_out = template.render(context)

    # 5. Gerar o PDF a partir do HTML
    # O base_url é crucial para o WeasyPrint encontrar o arquivo CSS
    pdf_bytes = HTML(string=html_out, base_url=str(template_path)).write_pdf()

    return pdf_bytes
