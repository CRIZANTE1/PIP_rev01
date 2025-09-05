import pandas as pd

def safe_to_numeric(value):
    """
    Converte um valor para numérico de forma segura, tratando vírgulas como decimais.
    Retorna 0.0 se a conversão falhar ou o valor for nulo.
    """
    if value is None:
        return 0.0
    # Garante que o valor seja uma string antes de substituir
    numeric_value = pd.to_numeric(str(value).replace(',', '.'), errors='coerce')
    return numeric_value if pd.notna(numeric_value) else 0.0
