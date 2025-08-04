import base64
import io
from weasyprint import HTML
import plotly.graph_objects as go
from operations.plot import criar_diagrama_guindaste

def get_status_class(status_text):
    """Retorna uma classe CSS baseada no status para colorir o texto."""
    if not status_text:
        return "warning"
    status_lower = status_text.lower()
    if "válido" in status_lower or "em dia" in status_lower:
        return "success"
    elif "vencido" in status_lower or "vencida" in status_lower:
        return "error"
    else:
        return "warning"

def generate_pdf_report(dados_icamento, form_data):
    """
    Gera um relatório em PDF a partir dos dados da sessão.

    Args:
        dados_icamento (dict): Dicionário com os resultados do cálculo de içamento.
        form_data (dict): Dicionário com todos os dados do formulário da Aba 2.

    Returns:
        bytes: O conteúdo do PDF gerado.
    """
    # 1. Gerar o gráfico do guindaste e converter para imagem base64
    fig = criar_diagrama_guindaste(
        dados_icamento.get('raio_max', 0),
        dados_icamento.get('alcance_max', 0),
        dados_icamento.get('carga_total', 0),
        dados_icamento.get('capacidade_raio', 0),
        dados_icamento.get('angulo_minimo_fabricante', 30)
    )
    
    img_bytes = fig.to_image(format="png", scale=2) # Aumentar a escala para melhor resolução
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    img_html = f'<img src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto;" />'

    # 2. Preparar dados para o template
    val = dados_icamento.get('validacao', {})
    detalhes_val = val.get('detalhes', {})

    # 3. Montar o template HTML com CSS inline
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Análise de Içamento</title>
        <style>
            @page {{ size: A4; margin: 1.5cm; }}
            body {{ font-family: 'Helvetica', sans-serif; color: #333; font-size: 11pt; }}
            h1 {{ color: #003366; text-align: center; border-bottom: 2px solid #003366; padding-bottom: 10px; }}
            h2 {{ color: #0055a4; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 25px; font-size: 14pt; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .container {{ display: flex; flex-wrap: wrap; }}
            .column {{ width: 48%; margin-right: 2%; }}
            .column:last-child {{ margin-right: 0; }}
            .highlight {{ background-color: #e6f7ff; font-weight: bold; }}
            .success {{ color: #28a745; font-weight: bold; }}
            .error {{ color: #dc3545; font-weight: bold; }}
            .warning {{ color: #ffc107; font-weight: bold; }}
            .footer {{ position: fixed; bottom: -1cm; left: 0; right: 0; text-align: center; font-size: 9pt; color: #888; }}
        </style>
    </head>
    <body>
        <div class="footer">
            Relatório gerado em {form_data.get('data_geracao')} | ID da Avaliação: {form_data.get('id_avaliacao')}
        </div>

        <h1>Relatório de Análise de Içamento de Carga</h1>

        <h2>Resumo do Cálculo de Carga</h2>
        <table>
            <tr><th>Descrição</th><th>Valor</th></tr>
            <tr><td>Peso da Carga</td><td>{dados_icamento.get('peso_carga', 0):.2f} kg</td></tr>
            <tr><td>Margem de Segurança</td><td>{dados_icamento.get('margem_seguranca_percentual', 0):.0f} %</td></tr>
            <tr><td>Peso de Segurança</td><td>{dados_icamento.get('peso_seguranca', 0):.2f} kg</td></tr>
            <tr><td>Peso a Considerar</td><td>{dados_icamento.get('peso_considerar', 0):.2f} kg</td></tr>
            <tr><td>Peso dos Cabos (3%)</td><td>{dados_icamento.get('peso_cabos', 0):.2f} kg</td></tr>
            <tr><td>Peso dos Acessórios</td><td>{dados_icamento.get('peso_acessorios', 0):.2f} kg</td></tr>
            <tr class="highlight"><td>CARGA TOTAL PARA IÇAMENTO</td><td>{dados_icamento.get('carga_total', 0):.2f} kg</td></tr>
        </table>

        <h2>Validação do Guindaste</h2>
        <p class="{get_status_class(val.get('mensagem'))}">{val.get('mensagem', 'N/A')}</p>
        <table>
            <tr><td>Utilização no Raio Máximo</td><td>{detalhes_val.get('porcentagem_raio', 0):.1f}%</td></tr>
            <tr><td>Utilização na Lança Máxima</td><td>{detalhes_val.get('porcentagem_alcance', 0):.1f}%</td></tr>
            <tr><td>Ângulo da Lança</td><td>{detalhes_val.get('angulo_lanca', 0):.1f}°</td></tr>
        </table>
        
        <h2>Diagrama da Operação</h2>
        {img_html}

        <div style="page-break-before: always;"></div>

        <h2>Informações da Operação</h2>
        <table>
            <tr><th colspan="2">Dados da Empresa</th></tr>
            <tr><td style="width: 30%;">Empresa</td><td>{form_data.get('empresa_form', 'N/A')}</td></tr>
            <tr><td>CNPJ</td><td>{form_data.get('cnpj_form', 'N/A')}</td></tr>
            
            <tr><th colspan="2">Dados do Operador</th></tr>
            <tr><td>Nome</td><td>{form_data.get('operador_form', 'N/A')}</td></tr>
            <tr><td>CPF</td><td>{form_data.get('cpf_form', 'N/A')}</td></tr>
            <tr><td>CNH</td><td>{form_data.get('cnh_form', 'N/A')}</td></tr>
            <tr><td>Validade CNH</td><td>{form_data.get('cnh_validade_form', 'N/A')} (<span class="{get_status_class(form_data.get('cnh_status'))}">{form_data.get('cnh_status', 'N/A')}</span>)</td></tr>

            <tr><th colspan="2">Dados do Equipamento</th></tr>
            <tr><td>Placa</td><td>{form_data.get('placa_form', 'N/A')}</td></tr>
            <tr><td>Fabricante</td><td>{form_data.get('fabricante_form', 'N/A')}</td></tr>
            <tr><td>Modelo</td><td>{form_data.get('modelo_form', 'N/A')}</td></tr>
            <tr><td>Ano</td><td>{form_data.get('ano_form', 'N/A')}</td></tr>

            <tr><th colspan="2">Documentação</th></tr>
            <tr><td>Nº ART</td><td>{form_data.get('art_num_form', 'N/A')}</td></tr>
            <tr><td>Validade ART</td><td>{form_data.get('art_validade_form', 'N/A')} (<span class="{get_status_class(form_data.get('art_status'))}">{form_data.get('art_status', 'N/A')}</span>)</td></tr>
            <tr><td>Módulo NR-11</td><td>{form_data.get('nr11_modulo_form', 'N/A')}</td></tr>
            <tr><td>Validade NR-11</td><td>{form_data.get('nr11_validade_form', 'N/A')} (<span class="{get_status_class(form_data.get('nr11_status'))}">{form_data.get('nr11_status', 'N/A')}</span>)</td></tr>
            <tr><td>Última Manutenção</td><td>{form_data.get('mprev_data_form', 'N/A')}</td></tr>
            <tr><td>Próxima Manutenção</td><td>{form_data.get('mprev_prox_form', 'N/A')} (<span class="{get_status_class(form_data.get('mprev_status'))}">{form_data.get('mprev_status', 'N/A')}</span>)</td></tr>
        </table>

        <h2>Observações Adicionais</h2>
        <p>{form_data.get('obs_form', 'Nenhuma observação foi registrada.')}</p>

    </body>
    </html>
    """

    # 4. Renderizar o HTML para PDF
    html = HTML(string=html_template)
    pdf_bytes = html.write_pdf()
    
    return pdf_bytes
