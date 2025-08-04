import plotly.graph_objects as go
import numpy as np

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
