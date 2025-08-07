from weasyprint import HTML, CSS
import pandas as pd
from datetime import datetime
import numpy as np
import base64


def generate_svg_diagram(raio_max, alcance_max, angulo_minimo_fabricante):
    """
    Gera o código SVG de um diagrama técnico a partir dos dados da operação.
    """
    if raio_max <= 0: raio_max = 1
    angulo_operacao_rad = np.arctan2(alcance_max, raio_max)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)
    angulo_min_rad = np.radians(angulo_minimo_fabricante)
    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2)

    svg_width = 800
    padding = 60
    scale = (svg_width - 2 * padding) / raio_max
    base_height = max(20, alcance_max * 0.05 * scale)
    svg_height = int(alcance_max * scale + base_height + 2 * padding)
    ox, oy = padding, svg_height - padding - base_height

    lan_x = ox + raio_max * scale
    lan_y = oy - alcance_max * scale
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    lanca_svg = f'<line x1="{ox}" y1="{oy}" x2="{lan_x}" y2="{lan_y}" stroke="{cor_lanca}" stroke-width="8" />'

    raio_risco_svg = comprimento_lanca * scale
    x_risco_end = ox + raio_risco_svg * np.cos(angulo_min_rad)
    y_risco_end = oy - raio_risco_svg * np.sin(angulo_min_rad)
    path_risco = f'M {ox},{oy} L {ox + raio_risco_svg},{oy} A {raio_risco_svg},{raio_risco_svg} 0 0 0 {x_risco_end},{y_risco_end} Z'
    zona_risco_svg = f'<path d="{path_risco}" fill="pink" fill-opacity="0.5" />'

    raio_arco_op_svg = comprimento_lanca * 0.25 * scale
    x_arco_end = ox + raio_arco_op_svg * np.cos(angulo_operacao_rad)
    y_arco_end = oy - raio_arco_op_svg * np.sin(angulo_operacao_rad)
    path_arco_op = f'M {ox + raio_arco_op_svg},{oy} A {raio_arco_op_svg},{raio_arco_op_svg} 0 0 1 {x_arco_end},{y_arco_end}'
    arco_op_svg = f'<path d="{path_arco_op}" fill="none" stroke="darkgreen" stroke-width="2" />'

    text_angle_rad_op = angulo_operacao_rad / 2
    text_x = ox + raio_arco_op_svg * 1.2 * np.cos(text_angle_rad_op)
    text_y = oy - raio_arco_op_svg * 1.2 * np.sin(text_angle_rad_op)
    texto_angulo_svg = f'<text x="{text_x}" y="{text_y}" fill="darkgreen" font-size="20" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{angulo_operacao_graus:.1f}°</text>'

    base_width_svg = max(30, raio_max * 0.05 * scale)
    base_svg = f'<rect x="{ox - base_width_svg/2}" y="{oy}" width="{base_width_svg}" height="{base_height*0.5}" fill="lightgray" /><rect x="{ox - 6}" y="{oy - base_height}" width="12" height="{base_height}" fill="dimgray" />'

    raio_line_y = oy + padding / 2
    raio_svg = f'<line x1="{ox}" y1="{raio_line_y}" x2="{lan_x}" y2="{raio_line_y}" stroke="black" stroke-width="1" stroke-dasharray="5,5" /><text x="{ox + (lan_x-ox)/2}" y="{raio_line_y + 15}" text-anchor="middle" font-size="14">Raio: {raio_max:.2f} m</text>'
    
    svg_code = f"""
    <svg width="100%" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">
        <style>.legend-text {{ font-size: 16px; }}</style>
        {zona_risco_svg} {lanca_svg} {base_svg} {arco_op_svg} {texto_angulo_svg} {raio_svg}
        <g transform="translate({padding}, 20)">
            <rect x="0" y="0" width="20" height="15" fill="royalblue" /><text x="30" y="12" class="legend-text">Lança de Operação</text>
            <rect x="0" y="25" width="20" height="15" fill="pink" fill-opacity="0.5" /><text x="30" y="37" class="legend-text">Zona de Risco (&lt; {angulo_minimo_fabricante}°)</text>
        </g>
    </svg>"""
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')}"

def safe_to_numeric(value):
    if value is None: return 0.0
    numeric_value = pd.to_numeric(str(value).replace(',', '.'), errors='coerce')
    return numeric_value if pd.notna(numeric_value) else 0.0

def get_report_html(context):
    # (O código desta função permanece o mesmo)
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
    <!DOCTYPE html><html lang="pt-br"><head><meta charset="UTF-8"><title>PAME - {context['id_avaliacao']}</title></head>
    <body><div class="report-container"><header class="report-header"><div class="logo-placeholder"><span class="logo-text">VIBRA</span></div><div class="title-container"><span class="main-title">PAME Manutenção e Instalações</span></div><div class="header-details"><span><strong>DATA:</strong> {context['data_emissao']}</span><span><strong>REV:</strong> 00</span><span><strong>FL:</strong> 1/1</span></div></header>
    <div class="main-content"><div class="left-column"><table class="data-table">
    <tr class="section-title"><td colspan="2">CONFIGURAÇÃO DO IÇAMENTO</td></tr>
    <tr><td class="label">Guindaste {fabricante}</td><td class="value">{nome_guindaste}</td></tr>
    <tr><td class="label">COMP. LANÇA / BOOM LENGTH</td><td class="value">{comp_lanca_mm}</td></tr>
    <tr><td class="label">RAIO DE OPERAÇÃO / RADIUS</td><td class="value">{raio_op_m}</td></tr>
    <tr><td class="label">CAPACIDADE DE CARGA / CAPACITY</td><td class="value">{capacidade_carga_kg}</td></tr>
    <tr><td class="label">PESO DA CARGA / MAX LOAD</td><td class="value">{peso_carga_kg}</td></tr>
    <tr><td class="label">PESO DO MOITÃO / BLOCK WEIGTH</td><td class="value">---</td></tr>
    <tr><td class="label">PESO DA LINGADA / RIGGING WEIGTH</td><td class="value">{peso_lingada_kg}</td></tr>
    <tr><td class="label">PESO TOTAL / TOTAL WEIGTH</td><td class="value">{carga_total_kg}</td></tr>
    <tr><td class="label">% DA CAPACIDADE / PERCENTAGE</td><td class="value">{perc_capacidade}</td></tr>
    <tr class="section-title"><td colspan="2">ESPECIFICAÇÃO DA LINGADA</td></tr>
    <tr><td class="label">ESTROPO 01</td><td class="value">---</td></tr><tr><td class="label">ESTROPO 02</td><td class="value">---</td></tr><tr><td class="label">BALANCIM / SPREADER BAR</td><td class="value">---</td></tr>
    <tr class="section-title"><td colspan="2">RESPONSABILIDADES / ASSINATURA</td></tr>
    <tr><td class="label">ELABORADO POR: RIGGER</td><td class="value" style="height: 25px;"></td></tr>
    <tr><td class="label">OPERADOR GUINDASTE</td><td class="value" style="height: 25px;"></td></tr>
    <tr><td class="label">SUPERVISOR DE MONTAGEM</td><td class="value" style="height: 25px;"></td></tr>
    <tr><td class="label">TÉC. DE SEGURANÇA</td><td class="value" style="height: 25px;"></td></tr>
    </table></div>
    <div class="right-column"><h2>Diagrama Técnico</h2><img src="{context['diagrama_base64']}" alt="Diagrama"></div></div>
    <footer class="report-footer"><div class="footer-box"><span class="label">CLIENTE:</span><span class="value large">VIBRA ENERGIA</span></div><div class="footer-box wide"><span class="label">TÍTULO:</span><span class="value large">ESTUDO DE RIGGING - {context['id_avaliacao']}</span><span class="value">PARA IÇAMENTO DE CARGA</span></div><div class="footer-box"><span class="label">LOCAL:</span><span class="value">ROD. CASTELO BRANCO - BARUERI/SP</span></div></footer>
    </div></body></html>
    """
    return html

def get_report_css():
    # (O código desta função permanece o mesmo)
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
    .right-column { flex: 1.5; border: 1px solid black; padding: 5px; text-align: center; }
    .right-column img { max-width: 100%; max-height: 95%; object-fit: contain; }
    .right-column h2 { font-size: 12pt; margin: 0 0 5px 0; }
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
    
    diagrama_base64_url = generate_svg_diagram(raio_max, alcance_max, angulo_minimo)

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
