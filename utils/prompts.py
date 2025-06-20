from datetime import date

def get_crlv_prompt():
    """Retorna o prompt para extrair dados de um CRLV."""
    return """
    Você é um assistente especialista em analisar documentos de veículos (CRLV).
    Extraia as seguintes informações do PDF:
    1. Placa do veículo.
    2. Ano de Fabricação.
    3. Marca / Modelo.
    Retorne a resposta APENAS em um formato JSON válido com as chaves "placa", "ano_fabricacao", "marca_modelo".
    Exemplo: {"placa": "ABC1D23", "ano_fabricacao": "2022", "marca_modelo": "M.BENZ/ATEGO 2426 6X2"}
    """

def get_art_prompt():
    """Retorna o prompt para extrair dados e status de validade de uma ART."""
    today = date.today().strftime("%Y-%m-%d")
    return f"""
    Você é um assistente especialista em analisar ARTs (Anotação de Responsabilidade Técnica).
    Analise o PDF e extraia:
    1. O número da ART.
    2. A data de validade final do documento. Se não houver data de validade, use a data de emissão/cadastro.
    3. Baseado na data de validade e na data de hoje ({today}), determine o status da ART.
    
    Retorne a resposta APENAS em um formato JSON válido com as chaves "numero_art", "validade_art" (formato "YYYY-MM-DD"), e "status" ("Válido", "Vencido", "Indeterminado").
    Exemplo: {{"numero_art": "SP20241234567", "validade_art": "2025-01-30", "status": "Válido"}}
    """

def get_cnh_prompt():
    """Retorna o prompt para extrair dados e status de validade de uma CNH."""
    today = date.today().strftime("%Y-%m-%d")
    return f"""
    Você é um assistente especialista em analisar CNH (Carteira Nacional de Habilitação).
    Analise o PDF e extraia:
    1. Nome completo do titular.
    2. CPF do titular.
    3. Número de Registro da CNH.
    4. A data de validade da CNH.
    5. Baseado na data de validade e na data de hoje ({today}), determine o status da CNH.
    
    Retorne a resposta APENAS em um formato JSON válido com as chaves "nome", "cpf", "numero_cnh", "validade_cnh" (YYYY-MM-DD), e "status" ("Válido", "Vencido").
    Exemplo: {{"nome": "JOAO DA SILVA", "cpf": "123.456.789-00", "numero_cnh": "01234567890", "validade_cnh": "2030-10-25", "status": "Válido"}}
    """

def get_nr11_prompt():
    """Retorna o prompt para extrair dados e status de validade de um Certificado NR-11."""
    today = date.today().strftime("%Y-%m-%d")
    return f"""
    Você é um assistente especialista em analisar certificados de treinamento de NR-11.
    Analise o PDF e extraia:
    1. Nome completo do operador.
    2. Número do certificado.
    3. A data de validade do certificado. Se não houver, calcule 1 ano a partir da data de emissão.
    4. Baseado na data de validade e na data de hoje ({today}), determine o status.
    
    Retorne a resposta APENAS em um formato JSON válido com as chaves "nome_operador", "numero_nr11", "validade_nr11" (YYYY-MM-DD), e "status" ("Válido", "Vencido", "Próximo ao Vencimento").
    Exemplo: {{"nome_operador": "CARLOS PEREIRA", "numero_nr11": "CERT-55443", "validade_nr11": "2024-11-14", "status": "Válido"}}
    """

def get_mprev_prompt():
    """Retorna o prompt para extrair dados e status de validade de um documento de Manutenção Preventiva."""
    today = date.today().strftime("%Y-%m-%d")
    return f"""
    Você é um assistente especialista em analisar relatórios de manutenção preventiva.
    Analise o PDF e extraia:
    1. A data em que a manutenção foi realizada.
    2. Calcule a data da próxima manutenção (exatamente 1 ano após a data da última).
    3. Baseado na data da próxima manutenção e na data de hoje ({today}), determine o status da manutenção.
    
    Retorne a resposta APENAS em um formato JSON válido com as chaves "data_ultima_manutencao" (YYYY-MM-DD), "data_proxima_manutencao" (YYYY-MM-DD), e "status" ("Em Dia", "Vencida").
    Exemplo: {{"data_ultima_manutencao": "2023-12-20", "data_proxima_manutencao": "2024-12-20", "status": "Em Dia"}}
    """
