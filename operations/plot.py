import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import io
import base64

def criar_diagrama_guindaste(raio_max, extensao_lanca, carga_total, capacidade_raio, angulo_minimo_fabricante):
    """
    Cria um diagrama técnico do guindaste com Plotly, com cálculos trigonométricos corretos.
    """
    fig = go.Figure()

    # --- 1. Validação de Dados ---
    if not all([raio_max > 0, extensao_lanca > 0]):
        fig.update_layout(title="Dados insuficientes para gerar o diagrama")
        return fig
        
    if extensao_lanca < raio_max:
        fig.update_layout(
            title_text=f"<b>Erro: Extensão da lança ({extensao_lanca}m) não pode ser menor que o raio ({raio_max}m)</b>", 
            title_x=0.5
        )
        return fig

    # --- 2. Cálculos Trigonométricos Corretos ---
    # Calcular a altura vertical (cateto oposto) usando Pitágoras
    altura_vertical = np.sqrt(extensao_lanca**2 - raio_max**2)
    
    # Calcular o ângulo da operação (em radianos e graus)
    angulo_operacao_rad = np.arccos(raio_max / extensao_lanca)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)
    
    # Converter ângulo mínimo do fabricante para radianos
    angulo_min_rad = np.radians(angulo_minimo_fabricante)

    # --- 3. Desenho dos Componentes ---
    # Definição de proporções para a base e torre
    base_width = max(4, raio_max * 0.1)
    torre_height = max(2, altura_vertical * 0.1)
    
    # Base e Torre do Guindaste
    fig.add_trace(go.Scatter(x=[-base_width/2, base_width/2, base_width/2, -base_width/2, -base_width/2], y=[-torre_height/2, -torre_height/2, 0, 0, -torre_height/2], mode='lines', name='Base', line=dict(color='darkgray', width=4), fill='toself', fillcolor='lightgray', hoverinfo='none'))
    fig.add_trace(go.Scatter(x=[0, 0], y=[0, torre_height], mode='lines', name='Torre', line=dict(color='dimgray', width=8), hoverinfo='none'))

    # Lança de Operação
    y_lan_end = torre_height + altura_vertical
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    fig.add_trace(go.Scatter(
        x=[0, raio_max], 
        y=[torre_height, y_lan_end],
        mode='lines+markers', 
        name='Lança de Operação',
        line=dict(color=cor_lanca, width=10),
        marker=dict(symbol='circle', size=8, color=cor_lanca),
        hovertemplate=f"<b>Lança de Operação</b><br>Comprimento: {extensao_lanca:.2f} m<br>Ângulo: {angulo_operacao_graus:.2f}°<extra></extra>"
    ))

    # Zona de Risco (Área abaixo do ângulo mínimo)
    # Gera 100 pontos entre a horizontal (0 rad) e o ângulo mínimo
    theta_risco = np.linspace(0, angulo_min_rad, 100)
    # Calcula as coordenadas x e y para formar um arco com o comprimento da lança
    x_risco_arc = extensao_lanca * np.cos(theta_risco)
    y_risco_arc = torre_height + extensao_lanca * np.sin(theta_risco)
    
    # Concatena o ponto inicial (0, torre_height) e final (0, torre_height) para fechar o polígono
    fig.add_trace(go.Scatter(
        x=np.concatenate([[0], x_risco_arc, [0]]),
        y=np.concatenate([[torre_height], y_risco_arc, [torre_height]]),
        mode='lines', 
        fill='toself', 
        fillcolor='rgba(220, 20, 60, 0.15)',
        line=dict(color='rgba(220, 20, 60, 0.3)'),
        name=f'Zona de Risco (< {angulo_minimo_fabricante}°)',
        hoverinfo='none'
    ))

    # --- 4. Anotações e Detalhes ---
    # Linha e texto para o Raio
    fig.add_shape(type="line", x0=0, y0=0, x1=raio_max, y1=0, line=dict(color="black", width=1, dash="dash"))
    fig.add_annotation(x=raio_max/2, y=0, text=f"<b>Raio: {raio_max:.2f} m</b>", showarrow=False, yshift=-20)
    
    # Arco do Ângulo da Operação
    arc_radius_op = extensao_lanca * 0.25 # Raio do arco de anotação
    theta_arco_op = np.linspace(0, angulo_operacao_rad, 50)
    x_arco_op = arc_radius_op * np.cos(theta_arco_op)
    y_arco_op = torre_height + arc_radius_op * np.sin(theta_arco_op)
    fig.add_trace(go.Scatter(x=x_arco_op, y=y_arco_op, mode='lines', line=dict(color='darkgreen', width=2), hoverinfo='none', showlegend=False))
    
    # Texto do Ângulo da Operação
    text_angle_rad_op = angulo_operacao_rad / 2
    fig.add_annotation(
        x=arc_radius_op * 1.2 * np.cos(text_angle_rad_op),
        y=torre_height + arc_radius_op * 1.2 * np.sin(text_angle_rad_op),
        text=f"<b>{angulo_operacao_graus:.1f}°</b>",
        showarrow=False, 
        font=dict(color='darkgreen', size=14)
    )

    # Ponto de Içamento (Carga)
    fig.add_trace(go.Scatter(
        x=[raio_max], 
        y=[y_lan_end], 
        mode='markers', 
        name='Ponto de Içamento', 
        marker=dict(symbol='circle-open', size=15, color='darkorange', line=dict(width=3)), 
        hovertemplate=f"<b>Carga Total: {carga_total:,.2f} kg</b><br>Capacidade no Raio: {capacidade_raio:,.2f} kg<extra></extra>"
    ))

    # --- 5. Layout Final ---
    fig.update_layout(
        title=dict(text="<b>Diagrama Técnico da Operação de Içamento</b>", font=dict(size=20), x=0.5),
        xaxis_title="Distância Horizontal (Raio) [m]", 
        yaxis_title="Altura Vertical [m]",
        showlegend=True, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[-base_width, raio_max * 1.15], gridcolor='lightgrey'),
        yaxis=dict(range=[-torre_height, y_lan_end * 1.15], scaleanchor="x", scaleratio=1, gridcolor='lightgrey'),
        margin=dict(l=80, r=40, t=80, b=80), 
        hovermode='closest', 
        plot_bgcolor='white'
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
