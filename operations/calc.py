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

def validar_guindaste(carga_total, capacidade_raio, capacidade_alcance_max, raio_max=None, extensao_lanca=None, angulo_minimo_fabricante=None):
    """Valida se o guindaste é adequado com base em sua capacidade e ângulo."""

    if carga_total <= 0:
        raise ValueError("A carga total deve ser um valor positivo.")
    if capacidade_raio <= 0 or capacidade_alcance_max <= 0:
        raise ValueError("As capacidades do guindaste devem ser valores positivos.")
    
    if extensao_lanca < raio_max:
        raise ValueError(f"A extensão da lança ({extensao_lanca}m) não pode ser menor que o raio de operação ({raio_max}m).")


    angulo = np.degrees(np.arccos(raio_max / extensao_lanca))
    
    angulo_seguro = angulo >= angulo_minimo_fabricante 

    porcentagem_raio = (carga_total / capacidade_raio) * 100
    porcentagem_alcance_max = (carga_total / capacidade_alcance_max) * 100
    porcentagem_segura = max(porcentagem_raio, porcentagem_alcance_max)
    
    if not angulo_seguro:
        mensagem = f"ATENÇÃO: Ângulo da lança ({angulo:.1f}°) inferior ao mínimo de segurança do fabricante ({angulo_minimo_fabricante}°). Operação não segura."
        adequado = False
    elif porcentagem_segura > 80:
        mensagem = "ATENÇÃO: A carga excede 80% da capacidade do guindaste. Consulte a engenharia e equipe de segurança."
        adequado = False
    else:
        mensagem = "Guindaste adequado para o içamento."
        adequado = True

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
            'angulo_seguro': angulo_seguro,
            'angulo_minimo_fabricante': angulo_minimo_fabricante
        }
    }


