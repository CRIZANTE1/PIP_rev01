import numpy as np
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calcular_carga_total(peso_carga, equipamento_novo=True, peso_acessorios=0):
    """
    Calcula a carga total considerando margens de segurança e acessórios.
    
    Args:
        peso_carga (float): Peso principal da carga em kg
        equipamento_novo (bool): True para equipamento novo (10% margem), 
                                False para usado (25% margem)
        peso_acessorios (float): Peso dos acessórios (cintas, grilhetas, etc.) em kg
    
    Returns:
        dict: Dicionário com todos os valores calculados
    
    Raises:
        ValueError: Se os valores de entrada forem inválidos
    """
    # Validações de entrada
    if not isinstance(peso_carga, (int, float)):
        raise ValueError(f"O peso da carga deve ser um número. Recebido: {type(peso_carga)}")
    
    if peso_carga <= 0:
        raise ValueError(f"O peso da carga deve ser um valor positivo. Recebido: {peso_carga}")
    
    if not isinstance(peso_acessorios, (int, float)):
        raise ValueError(f"O peso dos acessórios deve ser um número. Recebido: {type(peso_acessorios)}")
    
    if peso_acessorios < 0:
        raise ValueError(f"O peso dos acessórios não pode ser negativo. Recebido: {peso_acessorios}")
    
    if not isinstance(equipamento_novo, bool):
        raise ValueError(f"equipamento_novo deve ser True ou False. Recebido: {equipamento_novo}")
    
    try:
        # Definição da margem de segurança
        margem_seguranca = 0.10 if equipamento_novo else 0.25
        
        # Cálculo do peso com margem de segurança
        peso_seguranca = peso_carga * margem_seguranca
        peso_considerar = peso_carga + peso_seguranca
        
        # Cálculo do peso dos cabos (3% do peso a considerar)
        peso_cabos = peso_considerar * 0.03
        
        # Cálculo da carga total
        carga_total = peso_considerar + peso_acessorios + peso_cabos
        
        # Log para auditoria
        logger.info(
            f"Cálculo de carga: Peso={peso_carga}kg, "
            f"Margem={margem_seguranca*100}%, "
            f"Acessórios={peso_acessorios}kg, "
            f"Total={carga_total:.2f}kg"
        )
        
        return {
            'peso_carga': peso_carga,
            'peso_seguranca': peso_seguranca,
            'peso_considerar': peso_considerar,
            'peso_cabos': peso_cabos,
            'peso_acessorios': peso_acessorios,
            'carga_total': carga_total,
            'margem_seguranca_percentual': margem_seguranca * 100
        }
        
    except Exception as e:
        logger.error(f"Erro no cálculo de carga total: {e}")
        raise


def validar_guindaste(carga_total, capacidade_raio, capacidade_alcance_max, 
                      raio_max, extensao_lanca, angulo_minimo_fabricante):
    """
    Valida se o guindaste é adequado com base em sua capacidade e ângulo, com zonas de segurança.
    
    Args:
        carga_total (float): Carga total calculada em kg
        capacidade_raio (float): Capacidade do guindaste no raio especificado em kg
        capacidade_alcance_max (float): Capacidade no alcance máximo da lança em kg
        raio_max (float): Raio de operação em metros
        extensao_lanca (float): Extensão total da lança em metros
        angulo_minimo_fabricante (float): Ângulo mínimo de segurança especificado em graus
    
    Returns:
        dict: Dicionário com resultados da validação e detalhes
    
    Raises:
        ValueError: Se os valores de entrada forem inválidos
    """
    
    # ==================== VALIDAÇÕES DE ENTRADA ====================
    
    # Validação de tipos
    validacoes_tipo = [
        (carga_total, "carga_total"),
        (capacidade_raio, "capacidade_raio"),
        (capacidade_alcance_max, "capacidade_alcance_max"),
        (raio_max, "raio_max"),
        (extensao_lanca, "extensao_lanca"),
        (angulo_minimo_fabricante, "angulo_minimo_fabricante")
    ]
    
    for valor, nome in validacoes_tipo:
        if not isinstance(valor, (int, float)):
            raise ValueError(f"{nome} deve ser um número. Recebido: {type(valor)}")
    
    # Validação de valores positivos
    if carga_total <= 0:
        raise ValueError(f"A carga total deve ser um valor positivo. Recebido: {carga_total}")
    
    if capacidade_raio <= 0:
        raise ValueError(f"A capacidade no raio deve ser um valor positivo. Recebido: {capacidade_raio}")
    
    if capacidade_alcance_max <= 0:
        raise ValueError(f"A capacidade no alcance deve ser um valor positivo. Recebido: {capacidade_alcance_max}")
    
    if raio_max <= 0:
        raise ValueError(f"O raio de operação deve ser um valor positivo. Recebido: {raio_max}")
    
    if extensao_lanca <= 0:
        raise ValueError(f"A extensão da lança deve ser um valor positivo. Recebido: {extensao_lanca}")
    
    # Validação do ângulo mínimo (deve estar entre 1 e 89 graus)
    if not (1 <= angulo_minimo_fabricante <= 89):
        raise ValueError(
            f"O ângulo mínimo deve estar entre 1° e 89°. Recebido: {angulo_minimo_fabricante}°"
        )
    
    # Validação geométrica crítica: raio não pode ser maior que a lança
    if raio_max > extensao_lanca:
        raise ValueError(
            f"Configuração geometricamente impossível: o raio de operação ({raio_max}m) "
            f"não pode ser maior que a extensão da lança ({extensao_lanca}m)."
        )
    
    # ==================== CÁLCULOS TRIGONOMÉTRICOS ====================
    
    try:
        # Cálculo da razão para o arco cosseno
        razao = raio_max / extensao_lanca
        
        # Proteção adicional: garantir que a razão está no domínio válido [-1, 1]
        # Isso evita erros numéricos de ponto flutuante
        razao_segura = np.clip(razao, -1.0, 1.0)
        
        # Cálculo do ângulo da lança em relação à horizontal
        angulo_rad = np.arccos(razao_segura)
        angulo = np.degrees(angulo_rad)
        
        logger.info(
            f"Cálculo de ângulo: Raio={raio_max}m, "
            f"Lança={extensao_lanca}m, "
            f"Ângulo calculado={angulo:.2f}°"
        )
        
    except Exception as e:
        logger.error(f"Erro no cálculo trigonométrico: {e}")
        raise ValueError(f"Erro ao calcular o ângulo da lança: {e}")
    
    # ==================== VALIDAÇÃO DE ÂNGULO ====================
    
    # Define a zona de atenção (5° acima do mínimo)
    MARGEM_ANGULO_ATENCAO = 5.0
    angulo_zona_atencao = angulo_minimo_fabricante + MARGEM_ANGULO_ATENCAO
    
    adequado = True
    mensagem = ""
    
    # 1. Verifica se está ABAIXO do mínimo (INSEGURO)
    if angulo < angulo_minimo_fabricante:
        adequado = False
        mensagem = (
            f"OPERAÇÃO INSEGURA: O ângulo da lança ({angulo:.1f}°) está ABAIXO "
            f"do mínimo permitido pelo fabricante ({angulo_minimo_fabricante}°). "
            f"Esta configuração pode causar tombamento do equipamento."
        )
        logger.warning(f"Ângulo inseguro detectado: {angulo:.1f}° < {angulo_minimo_fabricante}°")
    
    # 2. Verifica se está na ZONA DE ATENÇÃO (próximo ao limite)
    elif angulo < angulo_zona_atencao:
        adequado = True  # Tecnicamente válido, mas requer atenção
        mensagem = (
            f"ATENÇÃO: O ângulo da lança ({angulo:.1f}°) está muito próximo "
            f"do limite mínimo de segurança ({angulo_minimo_fabricante}°). "
            f"Recomenda-se maior margem de segurança."
        )
        logger.warning(f"Ângulo na zona de atenção: {angulo:.1f}°")
    
    else:
        mensagem = f"Ângulo da lança adequado ({angulo:.1f}°)."
    
    # ==================== VALIDAÇÃO DE CAPACIDADE ====================
    
    # Calcula as porcentagens de utilização
    porcentagem_raio = (carga_total / capacidade_raio) * 100
    porcentagem_alcance_max = (carga_total / capacidade_alcance_max) * 100
    
    # A porcentagem crítica é a maior entre as duas
    porcentagem_segura = max(porcentagem_raio, porcentagem_alcance_max)
    
    # Define limite de segurança em 80%
    LIMITE_SEGURANCA = 80.0
    
    # Verifica se excede o limite de 80%
    if porcentagem_segura > LIMITE_SEGURANCA:
        adequado = False
        mensagem = (
            f"OPERAÇÃO INSEGURA: A carga ({carga_total:.2f}kg) excede {LIMITE_SEGURANCA}% "
            f"da capacidade do guindaste. Utilização atual: {porcentagem_segura:.1f}%. "
            f"Esta operação requer análise adicional da engenharia."
        )
        logger.warning(
            f"Capacidade excedida: {porcentagem_segura:.1f}% "
            f"(Raio: {porcentagem_raio:.1f}%, Alcance: {porcentagem_alcance_max:.1f}%)"
        )
    
    # Se já estava com problema de ângulo, mantém a mensagem de ângulo
    # mas adiciona informação de capacidade se também for problema
    if "INSEGURA" in mensagem and porcentagem_segura > LIMITE_SEGURANCA:
        mensagem += f" Adicionalmente, a utilização da capacidade está em {porcentagem_segura:.1f}%."
    
    # ==================== PREPARAÇÃO DO RESULTADO ====================
    
    resultado = {
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
            'angulo_minimo_fabricante': angulo_minimo_fabricante,
            'na_zona_atencao': angulo < angulo_zona_atencao and angulo >= angulo_minimo_fabricante
        }
    }
    
    # Log do resultado final
    status = "ADEQUADO" if adequado else "INADEQUADO"
    logger.info(
        f"Validação concluída: {status} | "
        f"Ângulo: {angulo:.1f}° | "
        f"Utilização: {porcentagem_segura:.1f}%"
    )
    
    return resultado


def verificar_configuracao_valida(raio_max, extensao_lanca):
    """
    Função auxiliar para verificar se a configuração geométrica é válida
    antes de realizar cálculos mais complexos.
    
    Args:
        raio_max (float): Raio de operação em metros
        extensao_lanca (float): Extensão da lança em metros
    
    Returns:
        tuple: (bool, str) - (é_valido, mensagem_erro)
    """
    if raio_max <= 0 or extensao_lanca <= 0:
        return False, "Raio e extensão da lança devem ser valores positivos."
    
    if raio_max > extensao_lanca:
        return False, (
            f"Configuração impossível: raio ({raio_max}m) > "
            f"extensão da lança ({extensao_lanca}m)"
        )
    
    if raio_max == extensao_lanca:
        return False, (
            "Configuração crítica: raio igual à extensão da lança (ângulo 0°). "
            "Esta configuração é extremamente perigosa."
        )
    
    return True, "Configuração válida."


def calcular_fator_seguranca(carga_total, capacidade):
    """
    Calcula o fator de segurança da operação.
    
    Args:
        carga_total (float): Carga total em kg
        capacidade (float): Capacidade do equipamento em kg
    
    Returns:
        float: Fator de segurança (capacidade / carga)
    """
    if carga_total <= 0 or capacidade <= 0:
        raise ValueError("Valores devem ser positivos para cálculo do fator de segurança")
    
    return capacidade / carga_total




