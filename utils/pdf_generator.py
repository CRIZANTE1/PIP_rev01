from weasyprint import HTML, CSS
import pandas as pd
from datetime import datetime

# Importa a função centralizada e o plot estático
from utils.helpers import safe_to_numeric
from operations.plot import generate_static_diagram_for_pdf

def get_report_html(context):
    """
    Gera a string HTML completa do relatório usando f-strings e dados do contexto.
    """
    dados_icamento = context["dados_icamento"]
    dados_guindauto = context["dados_guindauto"]

    # Extração segura de dados com valores padrão
    peso_carga_f = f"{safe_to_numeric(dados_icamento.get('Peso Carga (kg)', 0)):.2f}"
    margem_perc_f = f"{safe_to_numeric(dados_icamento.get('Margem Segurança (%)', 0)):.0f}"
    peso_seguranca_f = f"{safe_to_numeric(dados_icamento.get('Peso Segurança (kg)', 0)):.2f}"
    peso_cabos_f = f"{safe_to_numeric(dados_icamento.get('Peso Cabos (kg)', 0)):.2f}"
    peso_acessorios_f = f"{safe_to_numeric(dados_icamento.get('Peso Acessórios (kg)', 0)):.2f}"
    carga_total_f = f"{safe_to_numeric(dados_icamento.get('Carga Total (kg)', 0)):.2f}"

    utilizacao_raio = dados_icamento.get('% Utilização Raio', 'N/A')
    utilizacao_alcance = dados_icamento.get('% Utilização Alcance', 'N/A')

    adequado_str = str(dados_icamento.get('Adequado', 'FALSE')).strip().upper()
    conclusao_status = "APROVADA" if adequado_str == 'TRUE' else "REPROVADA"

    try:
        util_raio_float = float(str(utilizacao_raio).replace('%', '').strip())
        util_alcance_float = float(str(utilizacao_alcance).replace('%', '').strip())
        limite_seguranca = "dentro dos limites de segurança de 80%" if max(util_raio_float, util_alcance_float) <= 80 else "excedendo o limite de segurança de 80%"
    except (ValueError, TypeError):
        limite_seguranca = "com limites de segurança indeterminados"

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Análise de Içamento - {context['id_avaliacao']}</title>
    </head>
    <body>
        <!-- Capa do Relatório -->
        <div class="cover-page">
            <h1>VIBRA ENERGIA</h1>
            <br><br><br><br>
            <h2>RELATÓRIO DE ANÁLISE TÉCNICA DE IÇAMENTO DE CARGA</h2>
            <h3>ID da Avaliação: {context['id_avaliacao']}</h3>
            <p><strong>Empresa Contratante:</strong> {dados_guindauto.get('Empresa', 'Não informado')}</p>
            <br><br><br><br><br><br>
            <p class="cover-footer">{context['cidade']}, {context['data_emissao']}</p>
        </div>

        <!-- Introdução -->
        <section>
            <h1>1. INTRODUÇÃO</h1>
            <p>
                Este relatório apresenta a análise técnica e a metodologia aplicada na avaliação da operação de
                içamento de carga, identificada pelo ID {context['id_avaliacao']}. O objetivo deste documento é validar
                a segurança e a conformidade dos equipamentos e procedimentos utilizados, com base nos dados
                fornecidos e nos cálculos de engenharia realizados. A elaboração deste relatório é de responsabilidade da VIBRA ENERGIA.
            </p>
        </section>

        <!-- Desenvolvimento -->
        <section>
            <h1>2. DESENVOLVIMENTO</h1>
            <div class="content-wrapper">
                <div class="column-left">
                    <h2>2.1. Dados da Operação</h2>
                    <p>A operação foi realizada com os seguintes parâmetros principais:</p>
                    <ul>
                        <li><strong>Operador Responsável:</strong> {dados_guindauto.get('Nome Operador', 'Não informado')}</li>
                        <li><strong>Guindaste Utilizado:</strong> {dados_icamento.get('Fabricante Guindaste', 'N/A')} - {dados_icamento.get('Nome Guindaste', 'N/A')}</li>
                        <li><strong>Placa do Veículo:</strong> {dados_guindauto.get('Placa Guindaste', 'Não informado')}</li>
                    </ul>

                    <h2>2.2. Metodologia de Cálculo de Carga</h2>
                    <p>A carga total da operação foi determinada pela soma do peso da carga, acessórios, cabos e uma margem de segurança. Os valores calculados foram:</p>
                    <table>
                        <tr><td>Peso da Carga</td><td>{peso_carga_f} kg</td></tr>
                        <tr><td>Margem de Segurança ({margem_perc_f}%)</td><td>{peso_seguranca_f} kg</td></tr>
                        <tr><td>Peso dos Cabos</td><td>{peso_cabos_f} kg</td></tr>
                        <tr><td>Peso dos Acessórios</td><td>{peso_acessorios_f} kg</td></tr>
                        <tr class="total-row"><td><strong>Carga Total Calculada</strong></td><td><strong>{carga_total_f} kg</strong></td></tr>
                    </table>
                </div>
                <div class="column-right">
                    <h2>2.3. Diagrama e Análise de Capacidade</h2>
                    <p>O diagrama abaixo ilustra a configuração do içamento. A análise de capacidade indicou uma utilização de {utilizacao_raio} no raio máximo e {utilizacao_alcance} no alcance máximo.</p>
                    <img src="{context['diagrama_base64']}" alt="Diagrama de Içamento">
                </div>
            </div>
        </section>

        <!-- Conclusão -->
        <section>
            <h1>3. CONCLUSÃO</h1>
            <p>
                Com base na análise dos dados e nos cálculos realizados, a operação foi considerada
                <strong>{conclusao_status}</strong>.
                A carga total de {carga_total_f} kg está {limite_seguranca} da capacidade do equipamento nas configurações avaliadas.
            </p>
            <p>Recomenda-se que todos os procedimentos de segurança padrão sejam seguidos durante a execução da tarefa.</p>
        </section>
    </body>
    </html>
    """
    return html

def get_report_css():
    """
    Retorna a string CSS com estilos ABNT para o relatório.
    """
    css = """
    @page {
        size: A4 landscape;
        margin: 2cm;
        @bottom-right {
            content: counter(page);
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
        }
    }
    body {
        font-family: 'Times New Roman', serif;
        font-size: 12pt;
        line-height: 1.5;
        text-align: justify;
    }
    h1, h2, h3 {
        font-family: 'Arial', sans-serif;
        color: #333;
        font-weight: bold;
        text-align: left;
    }
    h1 { font-size: 14pt; margin-top: 24pt; }
    h2 { font-size: 12pt; margin-top: 18pt; }
    p { text-indent: 4em; margin-bottom: 12pt; }
    ul { list-style-position: inside; padding-left: 4em; }
    .cover-page {
        page-break-after: always;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    .cover-page h1, .cover-page h2, .cover-page h3 { text-align: center; }
    .cover-footer { text-indent: 0; margin-top: auto; }
    img { max-width: 95%; height: auto; display: block; margin: 10px auto; border: 1px solid #ccc; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; }
    td { border: 1px solid #ccc; padding: 8px; }
    .total-row { background-color: #f2f2f2; }
    .content-wrapper { display: flex; flex-direction: row; gap: 20px; }
    .column-left { flex: 1; }
    .column-right { flex: 1.2; }
    """
    return css

def generate_abnt_report(dados_icamento, dados_guindauto):
    """
    Função principal que orquestra a geração do relatório PDF em formato ABNT.
    """
    # Usa a função centralizada para converter os dados
    raio_max = safe_to_numeric(dados_icamento.get('Raio Máximo (m)'))
    alcance_max = safe_to_numeric(dados_icamento.get('Alcance Máximo (m)'))
    angulo_minimo = safe_to_numeric(dados_icamento.get('Ângulo Mínimo da Lança'))
    if pd.isna(angulo_minimo) or angulo_minimo == 0:
        angulo_minimo = 40.0 # Define um padrão seguro caso o dado não exista

    diagrama_base64_url = generate_static_diagram_for_pdf(raio_max, alcance_max, angulo_minimo)

    context = {
        "id_avaliacao": dados_icamento.name,
        "cidade": "Barueri, SP",
        "data_emissao": datetime.now().strftime("%d de %B de %Y"),
        "dados_icamento": dados_icamento,
        "dados_guindauto": dados_guindauto,
        "diagrama_base64": diagrama_base64_url
    }

    html_string = get_report_html(context)
    css_string = get_report_css()

    css = CSS(string=css_string)
    pdf_bytes = HTML(string=html_string).write_pdf(stylesheets=[css])

    return pdf_bytes
