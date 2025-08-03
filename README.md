# Calculadora de Movimentação de Carga (PIP_rev1)

## 📋 Descrição
Uma aplicação web desenvolvida com Streamlit para auxiliar no cálculo e validação de operações de içamento com guindastes e guindautos. O sistema incorpora cálculos de segurança, validações técnicas e gerenciamento de documentação, tornando o processo mais seguro e eficiente.

## 🌟 Funcionalidades Principais

### Cálculos e Validações
- **Cálculo de Carga Total**
  - Peso da carga principal
  - Peso dos acessórios (cintas, grilhetas, etc.)
  - Peso dos cabos (calculado automaticamente como 3%)
  - Margens de segurança diferenciadas:
    - Equipamentos novos: 10%
    - Equipamentos usados: 25%

### Validação do Guindaste
- Verificação automática da adequação do equipamento
- Análise de capacidade baseada em:
  - Raio de operação
  - Alcance da lança
  - Capacidades nominais do equipamento

### Documentação e Registros
- Gerenciamento de documentos técnicos
- Registro de informações do operador e equipamento
- Armazenamento de certificados e ARTs
- Histórico completo de operações

### Interface Visual
- Diagrama ilustrativo da operação
- Indicadores visuais de segurança
- Dashboard interativo
- Histórico de avaliações

## 🛠️ Requisitos Técnicos

### Dependências Principais
```txt
streamlit>=1.28.0
numpy>=1.24.0
plotly>=5.18.0
pandas>=2.0.0
openpyxl>=3.1.0
google-api-python-client>=2.108.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.1.0
```

## 🚀 Instalação e Configuração

### 1. Configuração do Ambiente
```bash
# Clone o repositório
git clone [URL_DO_REPOSITÓRIO]

# Entre no diretório
cd PIP_rev0

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração do Google Drive e Sheets

#### 2.1 Criar Projeto no Google Cloud
1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto
3. Ative as APIs:
   - Google Drive API
   - Google Sheets API

#### 2.2 Configurar Conta de Serviço
1. No Console do Google Cloud:
   - Vá para "IAM & Admin" > "Service Accounts"
   - Crie uma nova conta de serviço
   - Baixe o arquivo JSON de credenciais

#### 2.3 Configurar Permissões
1. Compartilhe a pasta do Google Drive com o email da conta de serviço
2. Compartilhe a planilha do Google Sheets com o email da conta de serviço
3. Conceda permissões de editor em ambos

### 3. Configuração do Streamlit

#### 3.1 Local
Crie um arquivo `.streamlit/secrets.toml` com:
```toml
[connections.gsheets]
spreadsheet = "URL_DA_SUA_PLANILHA"
folder_id = "ID_DA_SUA_PASTA"

GOOGLE_SERVICE_ACCOUNT = "CONTEÚDO_DO_JSON_DE_CREDENCIAIS"
```

#### 3.2 Streamlit Cloud
Configure os mesmos secrets no dashboard do Streamlit Cloud:
1. Acesse as configurações do seu app
2. Vá para a seção "Secrets"
3. Adicione as mesmas configurações do arquivo local

## 🚦 Uso

1. Execute o aplicativo:
```bash
streamlit run main.py
```

2. Acesse através do navegador:
- Local: `http://localhost:8501`
- Cloud: URL fornecida pelo Streamlit Cloud

## 🔒 Segurança

- Todas as credenciais são gerenciadas de forma segura através do sistema de secrets do Streamlit
- As chaves de API nunca são expostas no código
- Autenticação OIDC para controle de acesso
- Logs de todas as operações realizadas

## 📊 Armazenamento de Dados

- Dados de içamento são salvos em planilhas Google Sheets
- Documentos são armazenados no Google Drive
- Backup automático de todas as operações
- Histórico completo disponível para consulta

## 👥 Suporte

Para suporte técnico ou dúvidas:
- Email: cristianfc2015@hotmail.com
- LinkedIn: [Cristian Ferreira Carlos](https://www.linkedin.com/in/cristian-ferreira-carlos-256b19161/)

## 📝 Licença

Copyright 2024, Cristian Ferreira Carlos, Todos os direitos reservados.

---

Desenvolvido por [Cristian Ferreira Carlos](https://www.linkedin.com/in/cristian-ferreira-carlos-256b19161/)
