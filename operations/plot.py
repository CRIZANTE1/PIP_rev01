import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import io
import base64

def generate_static_diagram_for_pdf(raio_max, alcance_max, angulo_minimo_fabricante):
    """
    CORREÇÃO: Cria um diagrama estático usando Matplotlib, que se adapta dinamicamente
    a qualquer escala de raio e alcance.
    """
    # Cálculos
    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2)
    angulo_operacao_rad = np.arctan2(alcance_max, raio_max)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)
    angulo_min_rad = np.radians(angulo_minimo_fabricante)

    # Criação da Figura
    fig, ax = plt.subplots(figsize=(10, 8)) # Aumentar o tamanho para melhor visualização
    ax.set_aspect('equal', adjustable='box')

    # Base e Torre do Guindaste
    # CORREÇÃO: A base agora é proporcional ao raio para não parecer minúscula
    base_width = max(4, raio_max * 0.05)
    torre_height = max(2, alcance_max * 0.05)
    ax.fill([-base_width/2, base_width/2, base_width/2, -base_width/2], [-torre_height/2, -torre_height/2, 0, 0], color='lightgray', zorder=1)
    ax.plot([0, 0], [0, torre_height], color='dimgray', linewidth=8, zorder=2)

    # Lança
    y_lan_end = torre_height + alcance_max
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    ax.plot([0, raio_max], [torre_height, y_lan_end], color=cor_lanca, linewidth=6, zorder=4, label='Lança de Operação')

    # Zona de Risco
    theta_risco = np.linspace(0, angulo_min_rad, 50)
    x_risco = comprimento_lanca * np.cos(theta_risco)
    y_risco = torre_height + comprimento_lanca * np.sin(theta_risco)
    ax.fill_between(x_risco, torre_height, y_risco, color='crimson', alpha=0.15, zorder=3, label=f'Zona de Risco (< {angulo_minimo_fabricante}°)')


    # Linhas de Raio e Altura
    # CORREÇÃO: Posicionamento do texto do raio se torna dinâmico
    ax.plot([0, raio_max], [-torre_height * 0.5, -torre_height * 0.5], color='black', linestyle='--', linewidth=1)
    ax.text(raio_max / 2, -torre_height * 0.8, f"Raio: {raio_max:.2f} m", ha='center', fontsize=9)

    # Arco do Ângulo
    # CORREÇÃO: Raio do arco e posição do texto agora são proporcionais ao comprimento da lança
    arc_radius = comprimento_lanca * 0.2
    arc = Arc((0, torre_height), arc_radius * 2, arc_radius * 2, angle=0, theta1=0, theta2=angulo_operacao_graus, color='darkgreen', linewidth=2)
    ax.add_patch(arc)
    text_angle_rad = angulo_operacao_rad / 2
    text_x = arc_radius * 1.15 * np.cos(text_angle_rad)
    text_y = torre_height + arc_radius * 1.15 * np.sin(text_angle_rad)
    ax.text(text_x, text_y, f'{angulo_operacao_graus:.1f}°', color='darkgreen', ha='center', va='center', fontsize=10, weight='bold')

    # Configurações do Gráfico
    ax.set_title("Diagrama Técnico da Operação de Içamento", fontsize=14)
    ax.set_xlabel("Distância Horizontal (Raio) [m]", fontsize=10)
    ax.set_ylabel("Altura Vertical [m]", fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=8)

    # Limites dos Eixos (A correção mais importante)
    # CORREÇÃO: Os limites agora se ajustam dinamicamente com uma margem de 10%
    ax.set_xlim(-raio_max * 0.1, raio_max * 1.1)
    ax.set_ylim(-torre_height, y_lan_end * 1.1)

    # Salvar a figura em um buffer de memória
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200, bbox_inches='tight') # Aumentar DPI para qualidade
    buf.seek(0)
    plt.close(fig) # Fechar a figura para liberar memória

    # Converter para base64
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"




def criar_diagrama_guindaste(raio_max, alcance_max, carga_total, capacidade_raio, angulo_minimo_fabricante):
    """
    Cria um diagrama técnico avançado do guindaste com simulação de içamento.
    """
    fig = go.Figure()

    # --- Validações e Cálculos Iniciais ---
    if not all([raio_max > 0, alcance_max > 0]):
        # Retorna uma figura vazia com uma mensagem se os dados forem inválidos
        fig.update_layout(
            title="Dados insuficientes para gerar o diagrama",
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': "Por favor, insira valores válidos para Raio e Alcance.",
                'xref': "paper", 'yref': "paper",
                'showarrow': False, 'font': {'size': 16}
            }]
        )
        return fig

    comprimento_lanca = np.sqrt(raio_max**2 + alcance_max**2)
    angulo_operacao_rad = np.arctan2(alcance_max, raio_max)
    angulo_operacao_graus = np.degrees(angulo_operacao_rad)

 
    fig.add_trace(go.Scatter(
        x=[-2, 2, 2, -2, -2], y=[-1, -1, 0, 0, -1],
        mode='lines', name='Base', line=dict(color='darkgray', width=4), fill='toself',
        fillcolor='lightgray', hoverinfo='none'
    ))
    # Torre do Guindaste
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[0, 2],
        mode='lines', name='Torre', line=dict(color='dimgray', width=8), hoverinfo='none'
    ))

  
    cor_lanca = 'royalblue' if angulo_operacao_graus >= angulo_minimo_fabricante else 'crimson'
    fig.add_trace(go.Scatter(
        x=[0, raio_max], y=[2, alcance_max + 2], 
        mode='lines+markers',
        name='Lança de Operação',
        line=dict(color=cor_lanca, width=10),
        marker=dict(symbol='circle', size=8, color=cor_lanca),
        hovertemplate=f"<b>Lança de Operação</b><br>Comprimento: {comprimento_lanca:.2f} m<br>Ângulo: {angulo_operacao_graus:.2f}°<extra></extra>"
    ))

   
    angulo_min_rad = np.radians(angulo_minimo_fabricante)
    theta_risco = np.linspace(0, angulo_min_rad, 50)
    x_risco = (comprimento_lanca + 2) * np.cos(theta_risco)
    y_risco = (comprimento_lanca + 2) * np.sin(theta_risco) + 2
    fig.add_trace(go.Scatter(
        x=np.concatenate([[0], x_risco, [0]]),
        y=np.concatenate([[2], y_risco, [2]]),
        mode='lines', fill='toself', fillcolor='rgba(220, 20, 60, 0.15)',
        line=dict(color='rgba(220, 20, 60, 0.3)'),
        name=f'Zona de Risco (< {angulo_minimo_fabricante}°)',
        hoverinfo='none'
    ))
    

    fig.add_trace(go.Scatter(
        x=[0, raio_max], y=[-0.5, -0.5],
        mode='lines', name='Raio', line=dict(color='black', dash='dash', width=1),
        hoverinfo='none'
    ))
    fig.add_annotation(
        x=raio_max / 2, y=-0.5, text=f"<b>Raio: {raio_max:.2f} m</b>",
        showarrow=False, yshift=-15, font=dict(color='black', size=12)
    )

 
    fig.add_trace(go.Scatter(
        x=[-0.5, -0.5], y=[0, alcance_max + 2],
        mode='lines', name='Altura', line=dict(color='black', dash='dash', width=1),
        hoverinfo='none'
    ))
    fig.add_annotation(
        x=-0.5, y=(alcance_max + 2) / 2, text=f"<b>Altura: {alcance_max + 2:.2f} m</b>",
        showarrow=False, xshift=-45, font=dict(color='black', size=12), textangle=-90
    )

  
    fig.add_trace(go.Scatter(
        x=[raio_max], y=[alcance_max + 2],
        mode='markers', name='Ponto de Içamento',
        marker=dict(symbol='circle-open', size=15, color='darkorange', line=dict(width=3)),
        hovertemplate=f"<b>Carga Total: {carga_total:,.2f} kg</b><br>Capacidade no Raio: {capacidade_raio:,.2f} kg<extra></extra>"
    ))
    
    
    theta_arco = np.linspace(0, angulo_operacao_rad, 50)
    x_arco = (comprimento_lanca * 0.2) * np.cos(theta_arco)
    y_arco = (comprimento_lanca * 0.2) * np.sin(theta_arco) + 2
    fig.add_trace(go.Scatter(
        x=x_arco, y=y_arco, mode='lines',
        line=dict(color='darkgreen', width=2),
        hoverinfo='none'
    ))
    fig.add_annotation(
        x=x_arco[-1] * 1.2, y=y_arco[-1], text=f"<b>{angulo_operacao_graus:.1f}°</b>",
        showarrow=False, font=dict(color='darkgreen', size=14)
    )
    
   
    fig.update_layout(
        title=dict(text="<b>Diagrama Técnico da Operação de Içamento</b>", font=dict(size=20), x=0.5),
        xaxis_title="Distância Horizontal (Raio) [m]",
        yaxis_title="Altura Vertical [m]",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            range=[-5, max(raio_max, 10) * 1.1],
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            range=[-2, max(alcance_max + 2, 10) * 1.1],
            scaleanchor="x",
            scaleratio=1,
            gridcolor='lightgrey'
        ),
        margin=dict(l=80, r=40, t=80, b=80),
        hovermode='closest',
        plot_bgcolor='white' 
    )

    return fig
