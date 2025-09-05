import numpy as np

def calcular_carga_total(peso_carga, equipamento_novo=True, peso_acessorios=0):
    """Calcula a carga total considerando margens de segurança e acessórios."""

    if peso_carga <= 0:
        raise ValueError("O peso da carga deve ser um valor positivo.")
        
    margem_seguranca = 0.10 if equipamento_novo else 0.25
    peso_seguranca = peso_carga * margem_seguranca
    peso_considerar = peso_carga + peso_seguranca
    peso_cabos = peso_considerar * 0.03
    carga_total = peso_considerar + peso_acessorios + peso_cabos

    return {
        'peso_carga': peso_carga,
        'peso_seguranca': peso_seguranca,
        'peso_considerar': peso_considerar,
        'peso_cabos': peso_cabos,
        'peso_acessorios': peso_acessorios,
        'carga_total': carga_total,
        'margem_seguranca_percentual': margem_seguranca * 100
    }

def validar_guindaste(carga_total, capacidade_raio, capacidade_alcance_max, raio_max, extensao_lanca, angulo_minimo_fabricante):
    """Valida se o guindaste é adequado com base em sua capacidade e ângulo, com zonas de segurança."""

    if carga_total <= 0:
        raise ValueError("A carga total deve ser um valor positivo.")
    if capacidade_raio <= 0 or capacidade_alcance_max <= 0:
        raise ValueError("As capacidades do guindaste devem ser valores positivos.")
    if extensao_lanca < raio_max:
        raise ValueError(f"A extensão da lança ({extensao_lanca}m) não pode ser menor que o raio de operação ({raio_max}m).")

    # --- LÓGICA DE VALIDAÇÃO DE ÂNGULO REFEITA ---

    angulo = np.degrees(np.arccos(raio_max / extensao_lanca))
    
    # Define a margem de segurança para a "Zona de Atenção"
    margem_angulo_atencao = 5.0 
    angulo_zona_atencao = angulo_minimo_fabricante + margem_angulo_atencao

    # 1. Verifica se a operação é francamente INSEGURA
    if angulo < angulo_minimo_fabricante:
        adequado = False
        mensagem = f"OPERAÇÃO INSEGURA: O ângulo da lança ({angulo:.1f}°) está ABAIXO do mínimo permitido pelo fabricante ({angulo_minimo_fabricante}°)."
    
    # 2. Verifica se está na ZONA DE ATENÇÃO (próximo ao limite)
    elif angulo < angulo_zona_atencao:
        adequado = True # A operação é tecnicamente válida, mas merece atenção
        mensagem = f"ATENÇÃO: O ângulo da lança ({angulo:.1f}°) está muito próximo do limite mínimo de segurança. Recomenda-se maior margem."

    else:
        adequado = True
        mensagem = "Guindaste adequado para o içamento."

    porcentagem_raio = (carga_total / capacidade_raio) * 100
    porcentagem_alcance_max = (carga_total / capacidade_alcance_max) * 100
    porcentagem_segura = max(porcentagem_raio, porcentagem_alcance_max)

    if porcentagem_segura > 80:
        adequado = False
        mensagem = f"OPERAÇÃO INSEGURA: A carga excede 80% da capacidade do guindaste. (Utilização: {porcentagem_segura:.1f}%)"
        
    return {
        'porcentagem_segura': porcentagem_segura,
        'adequado': adequado,
        'mensagem': mensagem,
        'detalhes': {
            'raio_max': raio_max,
            'extensao_lanca': extensao_lanca,
            'capacidade_raio': capacidade_raio,
            'capacidade_alcance': capacidade_alcance_max,
            'porcentagem_raio': porcentagem_raio,
            'porcentagem_alcance': porcentagem_alcance_max,
            'angulo_lanca': angulo,
            'angulo_minimo_fabricante': angulo_minimo_fabricante
        }
    }





