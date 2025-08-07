from weasyprint import HTML, CSS
import pandas as pd
from datetime import datetime
import base64
from pathlib import Path

import plotly.io as pio
from operations.plot import criar_diagrama_guindaste


def safe_to_numeric(value):
    if value is None: return 0.0
    numeric_value = pd.to_numeric(str(value).replace(',', '.'), errors='coerce')
    return numeric_value if pd.notna(numeric_value) else 0.0

def get_report_html(context):
    dados_icamento = context["dados_icamento"]
    dados_guindauto = context["dados_guindauto"]
    fabricante = dados_icamento.get('fabricante_guindaste', '---')
    nome_guindaste = dados_icamento.get('nome_guindaste', '---')
    comp_lanca_mm = f"{safe_to_numeric(dados_icamento.get('alcance_max')) * 1000:.0f} mm"
    raio_op_m = f"{safe_to_numeric(dados_icamento.get('raio_max')):.2f} m"
    capacidade_carga_kg = f"{safe_to_numeric(dados_icamento.get('capacidade_raio')):.2f} Kg"
    peso_carga_kg = f"{safe_to_numeric(dados_icamento.get('peso_carga')):.2f} Kg"
    peso_lingada_kg = f"{safe_to_numeric(dados_icamento.get('peso_acessorios')):.2f} Kg"
    carga_total_kg = f"{safe_to_numeric(dados_icamento.get('carga_total')):.2f} Kg"
    perc_capacidade = dados_icamento.get('% Utilização Raio', '---')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head><meta charset="UTF-8"><title>PAME - {context['id_avaliacao']}</title></head>
    <body>
        <div class="report-container">
            <header class="report-header">
                <div class="logo-placeholder"><span class="logo-text">VIBRA</span></div>
                <div class="title-container"><span class="main-title">PAME Manutenção e Instalações</span></div>
                <div class="header-details">
                    <span><strong>DATA:</strong> {context['data_emissao']}</span>
                    <span><strong>REV:</strong> 00</span>
                    <span><strong>FL:</strong> 1/1</span>
                </div>
            </header>
            <div class="main-content">
                <div class="left-column">
                    <table class="data-table">
                        <tr class="section-title"><td colspan="2">CONFIGURAÇÃO DO IÇAMENTO - LIFTING CONFIGURATION</td></tr>
                        <tr><td class="label">Guindaste {fabricante}</td><td class="value">{nome_guindaste}</td></tr>
                        <tr><td class="label">COMP. LANÇA / BOOM LENGTH</td><td class="value">{comp_lanca_mm}</td></tr>
                        <tr><td class="label">RAIO DE OPERAÇÃO / RADIUS</td><td class="value">{raio_op_m}</td></tr>
                        <tr><td class="label">CAPACIDADE DE CARGA / CAPACITY</td><td class="value">{capacidade_carga_kg}</td></tr>
                        <tr><td class="label">PESO DA CARGA / MAX LOAD</td><td class="value">{peso_carga_kg}</td></tr>
                        <tr><td class="label">PESO DO MOITÃO / BLOCK WEIGTH</td><td class="value">---</td></tr>
                        <tr><td class="label">PESO DA LINGADA / RIGGING WEIGTH</td><td class="value">{peso_lingada_kg}</td></tr>
                        <tr><td class="label">PESO TOTAL / TOTAL WEIGTH</td><td class="value">{carga_total_kg}</td></tr>
                        <tr><td class="label">% DA CAPACIDADE / PERCENTAGE</td><td class="value">{perc_capacidade}</td></tr>
                        <tr class="section-title"><td colspan="2">ESPECIFICAÇÃO DA LINGADA - RIGGING CONFIGURATION</td></tr>
                        <tr><td class="label">ESTROPO 01</td><td class="value">---</td></tr>
                        <tr><td class="label">ESTROPO 02</td><td class="value">---</td></tr>
                        <tr><td class="label">BALANCIM / SPREADER BAR</td><td class="value">---</td></tr>
                        <tr class="section-title"><td colspan="2">RESPONSABILIDADES / ASSINATURA</td></tr>
                        <tr><td class="label">ELABORADO POR: RIGGER</td><td class="value" style="height: 25px;"></td></tr>
                        <tr><td class="label">OPERADOR GUINDASTE</td><td class="value" style="height: 25px;"></td></tr>
                        <tr><td class="label">SUPERVISOR DE MONTAGEM</td><td class="value" style="height: 25px;"></td></tr>
                        <tr><td class="label">TÉC. DE SEGURANÇA</td><td class="value" style="height: 25px;"></td></tr>
                    </table>
                </div>
                <div class="right-column">
                    <img src="{context['diagrama_base64']}" alt="Diagrama de Içamento">
                </div>
            </div>
            <footer class="report-footer">
                <div class="footer-box">
                    <span class="label">CLIENTE:</span>
                    <span class="value large">VIBRA ENERGIA</span>
                </div>
                <div class="footer-box wide">
                    <span class="label">TÍTULO:</span>
                    <span class="value large">ESTUDO DE RIGGING - {context['id_avaliacao']}</span>
                    <span class="value">PARA IÇAMENTO DE CARGA</span>
                </div>
                <div class="footer-box">
                    <span class="label">LOCAL:</span>
                    <span class="value">ROD. CASTELO BRANCO - BARUERI/SP</span>
                </div>
            </footer>
        </div>
    </body>
    </html>
    """
    return html

def get_report_css():
    css = """
    @page { size: A3 landscape; margin: 1.5cm; }
    body { font-family: Arial, sans-serif; font-size: 11pt; color: #333; }
    .report-container { border: 2px solid black; height: 98%; display: flex; flex-direction: column; }
    .report-header { display: flex; border-bottom: 2px solid black; padding: 10px; align-items: center; }
    .logo-placeholder { border: 1px solid #ccc; padding: 15px 25px; text-align: center; }
    .logo-text { font-size: 22pt; font-weight: bold; }
    .title-container { flex-grow: 1; text-align: center; font-weight: bold; font-size: 18pt; }
    .header-details { display: flex; flex-direction: column; font-size: 10pt; text-align: right; gap: 5px; }
    .main-content { display: flex; flex-grow: 1; padding: 10px; gap: 10px; }
    .left-column { flex: 1; }
    .right-column { flex: 1.5; border: 1px solid black; padding: 5px; }
    .right-column img { width: 100%; height: 100%; object-fit: contain; }
    .data-table { width: 100%; height: 100%; border-collapse: collapse; border: 1px solid black; }
    .data-table td { border: 1px solid black; padding: 4px; vertical-align: middle; }
    .data-table .section-title td { background-color: #e0e0e0; font-weight: bold; text-align: center; font-size: 12pt; }
    .data-table .label { font-weight: bold; font-size: 10pt; width: 40%; }
    .data-table .value { text-align: center; font-size: 11pt; }
    .report-footer { display: flex; border-top: 2px solid black; }
    .footer-box { border-right: 2px solid black; padding: 5px; display: flex; flex-direction: column; flex: 1; }
    .footer-box.wide { flex: 2; }
    .footer-box:last-child { border-right: none; }
    .footer-box .label { font-size: 10pt; font-weight: bold; }
    .footer-box .value { font-size: 11pt; text-align: center; margin-top: 5px; }
    .footer-box .value.large { font-size: 14pt; font-weight: bold; }
    """
    return css

def generate_abnt_report(dados_icamento, dados_guindauto):
    raio_max = safe_to_numeric(dados_icamento.get('Raio Máximo (m)'))
    alcance_max = safe_to_numeric(dados_icamento.get('Alcance Máximo (m)'))
    angulo_minimo = safe_to_numeric(dados_icamento.get('Ângulo Mínimo da Lança'))
    if pd.isna(angulo_minimo): angulo_minimo = 40.0
    
    diagrama_base64_url = generate_static_diagram_for_pdf(raio_max, alcance_max, angulo_minimo)

    context = {
        "id_avaliacao": dados_icamento.name, "cidade": "Barueri, SP",
        "data_emissao": datetime.now().strftime("%d/%m/%Y"),
        "dados_icamento": dados_icamento, "dados_guindauto": dados_guindauto,
        "diagrama_base64": diagrama_base64_url
    }
    
    html_string = get_report_html(context)
    css_string = get_report_css()
    css = CSS(string=css_string)
    pdf_bytes = HTML(string=html_string).write_pdf(stylesheets=[css])
    
    return pdf_bytes
