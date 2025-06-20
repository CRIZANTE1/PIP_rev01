def get_crlv_prompt():
    """
    Retorna o prompt para extrair dados de um CRLV (Certificado de Registro e Licenciamento do Veículo).
    """
    return """
    Você é um assistente especialista em analisar documentos de veículos brasileiros (CRLV).
    Sua tarefa é extrair as seguintes informações do PDF do CRLV fornecido:
    1. Placa do veículo.
    2. Ano de Fabricação.
    3. Marca / Modelo.
    
    Analise o documento cuidadosamente. A "Marca/Modelo" geralmente está em um único campo.
    
    Retorne a resposta **APENAS** em um formato JSON válido, com as seguintes chaves:
    - "placa"
    - "ano_fabricacao"
    - "marca_modelo"
    
    Exemplo de saída:
    {
        "placa": "ABC1D23",
        "ano_fabricacao": "2022",
        "marca_modelo": "M.BENZ/ATEGO 2426 6X2"
    }

    Se uma informação não for encontrada, retorne uma string vazia ("") para o valor correspondente.
    Não adicione nenhum texto ou explicação antes ou depois do JSON.
    """

def get_art_prompt():
    """
    Retorna o prompt para extrair dados de uma ART (Anotação de Responsabilidade Técnica).
    """
    return """
    Você é um assistente especialista em analisar documentos de engenharia, especificamente a ART (Anotação de Responsabilidade Técnica) do sistema CONFEA/CREA.
    Sua tarefa é extrair as seguintes informações do PDF da ART fornecido:
    1. O número da ART.
    2. A data de emissão ou data de cadastro do documento.
    
    Analise o documento cuidadosamente. O número da ART é um identificador único. A data geralmente está próxima ao cabeçalho ou no final do documento.
    
    Retorne a resposta **APENAS** em um formato JSON válido, com as seguintes chaves:
    - "numero_art"
    - "data_emissao" (no formato "YYYY-MM-DD")
    
    Exemplo de saída:
    {
        "numero_art": "SP20241234567",
        "data_emissao": "2024-05-21"
    }

    Se uma informação não for encontrada, retorne uma string vazia ("") para o valor correspondente.
    Não adicione nenhum texto ou explicação antes ou depois do JSON.
    """

def get_cnh_prompt():
    """
    Retorna o prompt para extrair dados de uma CNH (Carteira Nacional de Habilitação).
    """
    return """
    Você é um assistente especialista em analisar CNH (Carteira Nacional de Habilitação) brasileira.
    Extraia as seguintes informações do PDF:
    1. Nome completo do condutor.
    2. Número da CNH.
    3. Validade da CNH (formato YYYY-MM-DD).
    4. CPF do condutor.

    Retorne a resposta APENAS em um formato JSON válido, com as seguintes chaves:
    - "nome"
    - "numero_cnh"
    - "validade"
    - "cpf"

    Exemplo de saída:
    {
        "nome": "João da Silva",
        "numero_cnh": "12345678900",
        "validade": "2027-05-21",
        "cpf": "123.456.789-00"
    }

    Se uma informação não for encontrada, retorne uma string vazia ("") para o valor correspondente.
    Não adicione nenhum texto ou explicação antes ou depois do JSON.
    """

def get_nr11_prompt():
    """
    Retorna o prompt para extrair dados de um Certificado NR-11.
    """
    return """
    Você é um assistente especialista em analisar Certificados NR-11 (Treinamento de Operador de Guindaste).
    Extraia as seguintes informações do PDF:
    1. Nome do operador.
    2. Número do certificado NR-11.
    3. Data de emissão do certificado (formato YYYY-MM-DD).
    4. Validade do certificado (formato YYYY-MM-DD), se disponível.

    Retorne a resposta APENAS em um formato JSON válido, com as seguintes chaves:
    - "nome_operador"
    - "numero_nr11"
    - "data_emissao"
    - "validade"

    Exemplo de saída:
    {
        "nome_operador": "João da Silva",
        "numero_nr11": "NR1120241234",
        "data_emissao": "2024-05-21",
        "validade": "2025-05-21"
    }

    Se uma informação não for encontrada, retorne uma string vazia ("") para o valor correspondente.
    Não adicione nenhum texto ou explicação antes ou depois do JSON.
    """