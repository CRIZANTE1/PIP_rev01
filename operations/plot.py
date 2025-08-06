import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import io
import base64

def criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo_fabricante):
    """
    CORREÇÃO v2: Cria um diagrama técnico do guindaste com Plotly, com cálculos trigonométricos corretos.
    """
    fig = go.Figure()

    if not all([raio_max > 0, alcance_max > 0]):
        fig.update_layout(title="Dados insuficientes para gerar o diagrama")
        return fig

    # Cálculos da operação ATUAL
    angulo_operacao_rad = np.arctan2(alcance_max, raio_max)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)

    # Cálculos para a ZONA DE RISCO (baseado no ângulo mínimo)
    # CORREÇÃO: Usar o ângulo mínimo fornecido para desenhar a zona de risco
    angulo_min_rad = np.radians(angulo_minimo_fabricante)

    # Base e Torre Proporcionais
    base_width = max(4, raio_max * 0.05)
    torre_height = max(2, alcance_max * 0.05)
    
    # Base e Torre do Guindaste
    fig.add_trace(go.Scatter(x=[-base_width/2, base_width/2, base_width/2, -base_width/2, -base_width/2], y=[-torre_height/2, -torre_height/2, 0, 0, -torre_height/2], mode='lines', name='Base', line=dict(color='darkgray', width=4), fill='toself', fillcolor='lightgray', hoverinfo='none'))
    fig.add_trace(go.Scatter(x=[0, 0], y=[0, torre_height], mode='lines', name='Torre', line=dict(color='dimgray', width=8), hoverinfo='none'))

    # Lança de Operação
    y_lan_end = torre_height + alcance_max
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2) # Comprimento real da lança nesta operação
    fig.add_trace(go.Scatter(
        x=[0, raio_max], y=[torre_height, y_lan_end],
        mode='lines+markers', name='Lança de Operação',
        line=dict(color=cor_lanca, width=10),
        marker=dict(symbol='circle', size=8, color=cor_lanca),
        hovertemplate=f"<b>Lança de Operação</b><br>Comprimento: {comprimento_lanca:.2f} m<br>Ângulo: {angulo_operacao_graus:.2f}°<extra></extra>"
    ))

    # Zona de Risco
    # CORREÇÃO: O raio do arco da zona de risco deve ser grande o suficiente para ser visível
    raio_risco = max(raio_max, alcance_max) * 1.2
    theta_risco = np.linspace(0, angulo_min_rad, 50)
    x_risco = raio_risco * np.cos(theta_risco)
    y_risco = torre_height + raio_risco * np.sin(theta_risco)
    fig.add_trace(go.Scatter(
        x=np.concatenate([[0], x_risco, [0]]),
        y=np.concatenate([[torre_height], y_risco, [torre_height]]),
        mode='lines', fill='toself', fillcolor='rgba(220, 20, 60, 0.15)',
        line=dict(color='rgba(220, 20, 60, 0.3)'),
        name=f'Zona de Risco (< {angulo_minimo_fabricante}°)',
        hoverinfo='none'
    ))

    # Anotações e Arco do Ângulo da OPERAÇÃO
    fig.add_shape(type="line", x0=0, y0=-torre_height*0.5, x1=raio_max, y1=-torre_height*0.5, line=dict(color="black", width=1, dash="dash"))
    fig.add_annotation(x=raio_max/2, y=-torre_height*0.5, text=f"<b>Raio: {raio_max:.2f} m</b>", showarrow=False, yshift=-10)
    
    # CORREÇÃO: O raio do arco do ângulo deve ser proporcional ao COMPRIMENTO DA LANÇA
    arc_radius_op = comprimento_lanca * 0.2
    theta_arco_op = np.linspace(0, angulo_operacao_rad, 50)
    x_arco_op = arc_radius_op * np.cos(theta_arco_op)
    y_arco_op = torre_height + arc_radius_op * np.sin(theta_arco_op)
    fig.add_trace(go.Scatter(x=x_arco_op, y=y_arco_op, mode='lines', line=dict(color='darkgreen', width=2), hoverinfo='none', showlegend=False))
    text_angle_rad_op = angulo_operacao_rad / 2
    fig.add_annotation(
        x=arc_radius_op * 1.15 * np.cos(text_angle_rad_op),
        y=torre_height + arc_radius_op * 1.15 * np.sin(text_angle_rad_op),
        text=f"<b>{angulo_operacao_graus:.1f}°</b>",
        showarrow=False, font=dict(color='darkgreen', size=14)
    )

    # Ponto de Içamento
    fig.add_trace(go.Scatter(x=[raio_max], y=[y_lan_end], mode='markers', name='Ponto de Içamento', marker=dict(symbol='circle-open', size=15, color='darkorange', line=dict(width=3)), hovertemplate=f"<b>Carga Total: {carga_total:,.2f} kg</b><br>Capacidade no Raio: {capacidade_raio:,.2f} kg<extra></extra>"))

    # Layout Final
    fig.update_layout(
        title=dict(text="<b>Diagrama Técnico da Operação de Içamento</b>", font=dict(size=20), x=0.5),
        xaxis_title="Distância Horizontal (Raio) [m]", yaxis_title="Altura Vertical [m]",
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[-raio_max * 0.1, raio_max * 1.1], gridcolor='lightgrey'),
        yaxis=dict(range=[-torre_height, y_lan_end * 1.1], scaleanchor="x", scaleratio=1, gridcolor='lightgrey'),
        margin=dict(l=80, r=40, t=80, b=80), hovermode='closest', plot_bgcolor='white'
    )
    return fig


def generate_static_diagram_for_pdf(raio_max, alcance_max, angulo_minimo_fabricante):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_aspect('equal', adjustable='box')
    angulo_operacao_rad = np.arctan2(alcance_max, raio_max)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)
    angulo_min_rad = np.radians(angulo_minimo_fabricante)
    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2)
    base_width = max(4, raio_max * 0.05)
    torre_height = max(2, alcance_max * 0.05)
    ax.fill([-base_width/2, base_width/2, base_width/2, -base_width/2], [-torre_height/2, -torre_height/2, 0, 0], color='lightgray', zorder=1)
    ax.plot([0, 0], [0, torre_height], color='dimgray', linewidth=8, zorder=2)
    y_lan_end = torre_height + alcance_max
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    ax.plot([0, raio_max], [torre_height, y_lan_end], color=cor_lanca, linewidth=8, zorder=4, label='Lança de Operação')
    raio_risco = comprimento_lanca
    theta_risco = np.linspace(0, angulo_min_rad, 50)
    x_risco_arc = raio_risco * np.cos(theta_risco)
    y_risco_arc = torre_height + raio_risco * np.sin(theta_risco)
    x_poly = np.concatenate([[0], x_risco_arc])
    y_poly = np.concatenate([[torre_height], y_risco_arc])
    ax.fill(x_poly, y_poly, color='pink', alpha=0.5, zorder=3, label=f'Zona de Risco (< {angulo_minimo_fabricante}°)')
    ax.plot([0, raio_max], [-torre_height * 0.5, -torre_height * 0.5], color='black', linestyle='--', linewidth=1)
    ax.text(raio_max / 2, -torre_height * 0.8, f"Raio: {raio_max:.2f} m", ha='center', fontsize=9)
    arc_radius_op = comprimento_lanca * 0.25
    arc_op = Arc((0, torre_height), arc_radius_op * 2, arc_radius_op * 2, angle=0, theta1=0, theta2=angulo_operacao_graus, color='darkgreen', linewidth=2)
    ax.add_patch(arc_op)
    text_angle_rad_op = angulo_operacao_rad / 2
    text_x = arc_radius_op * 1.2 * np.cos(text_angle_rad_op)
    text_y = torre_height + arc_radius_op * 1.2 * np.sin(text_angle_rad_op)
    ax.text(text_x, text_y, f'{angulo_operacao_graus:.1f}°', color='darkgreen', ha='center', va='center', fontsize=12, weight='bold')
    ax.set_title("Diagrama Técnico da Operação de Içamento", fontsize=14)
    ax.set_xlabel("Distância Horizontal (Raio) [m]", fontsize=10)
    ax.set_ylabel("Altura Vertical [m]", fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=10)
    ax.set_xlim(-raio_max * 0.1, raio_max * 1.1)
    ax.set_ylim(-torre_height, y_lan_end * 1.1)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"
