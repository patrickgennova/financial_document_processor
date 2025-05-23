# Financial Document Processor

[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Um microserviço eficiente para processamento de documentos financeiros usando Inteligência Artificial.

## 📋 Visão Geral

O Financial Document Processor é um microserviço Python que:

1. Consome mensagens do Kafka contendo documentos financeiros (em base64)
2. Decodifica e extrai texto desses documentos (extratos bancários, etc.)
3. Utiliza IA para extrair transações e categorizá-las com alta precisão
4. Persiste os resultados e notifica sistemas downstream via Kafka

Suas principais características incluem:

- **Arquitetura plugável de IA**: Alternar facilmente entre OpenAI, Gemini e Claude
- **Alto desempenho**: Processamento eficiente e otimizado para custo
- **Segurança e confiabilidade**: Design robusto para dados financeiros confidenciais
- **Escalabilidade**: Arquitetura totalmente assíncrona e pronta para horizontalização
- **Observabilidade**: Logging detalhado e métricas Prometheus

## 🏗️ Arquitetura

Este projeto segue os princípios da Arquitetura Hexagonal (Ports & Adapters):

```
                       ┌──────────────────────────────────┐
                       │                                  │
                       │          Domain Core             │
                       │                                  │
                       └───────────────┬──────────────────┘
                                       │
┌─────────────────────────────────────┼─────────────────────────────────────┐
│                                     │                                     │
│           Input Adapters            │         Output Adapters             │
│                                     │                                     │
│  ┌──────────────┐  ┌──────────────┐ │ ┌──────────────┐  ┌──────────────┐  │
│  │              │  │              │ │ │              │  │              │  │
│  │    Kafka     │  │    HTTP      │ │ │   Database   │  │    Kafka     │  │
│  │   Consumer   │  │     API      │ │ │              │  │   Producer   │  │
│  │              │  │              │ │ │              │  │              │  │
│  └──────────────┘  └──────────────┘ │ └──────────────┘  └──────────────┘  │
│                                     │                                     │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                      │
┌────────────────────────────────────┐│┌────────────────────────────────────┐
│                                    │││                                    │
│          AI Providers              │││       External Services            │
│                                    │││                                    │
│  ┌──────────────┐  ┌──────────────┐│││  ┌──────────────┐  ┌──────────────┐│
│  │              │  │              ││││  │              │  │              ││
│  │    OpenAI    │  │    Gemini    ││││  │  Monitoring  │  │    Tracing   ││
│  │              │  │              │││└─►│              │  │              ││
│  └──────────────┘  └──────────────┘││   └──────────────┘  └──────────────┘│
│                                    ││                                     │
│  ┌──────────────┐                  ││                                     │
│  │              │                  ││                                     │
│  │    Claude    │                  ││                                     │
│  │              │                  ││                                     │
│  └──────────────┘                  ││                                     │
│                                    ││                                     │
└────────────────────────────────────┘└─────────────────────────────────────┘
```

## 🚀 Instruções de Instalação

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose
- Acesso a um cluster Kafka
- Credenciais para APIs de IA (OpenAI, Gemini, Claude)

### Instalação com Docker Compose

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/financial-document-processor.git
   cd financial-document-processor
   ```

2. Configure suas variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais
   ```

3. Inicie os serviços:
   ```bash
   docker-compose up -d
   ```

### Instalação Manual

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/financial-document-processor.git
   cd financial-document-processor
   ```

2. Configure o ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -e .
   ```

4. Configure suas variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais
   ```

5. Execute o serviço:
   ```bash
   python -m financial_document_processor.main
   ```

## 📝 Uso e Configuração

### Formato da Mensagem Kafka

O serviço espera mensagens no seguinte formato JSON:

```json
{
  "id": 12345,
  "external_id": "44f437b5-a093-4a53-bc59-dd427f8e9c56",
  "user_id": 98765,
  "document_type": "bank_statement",
  "filename": "extrato-maio-2023.pdf",
  "content_type": "application/pdf",
  "file_content": "base64_encoded_string_here...",
  "categories": ["categoria1", "categoria2"],
  "status": "pending",
  "created_at": "2023-05-10T14:30:00Z",
  "updated_at": "2023-05-10T14:30:00Z"
}
```

Campos importantes:
- `document_type`: Tipo de documento (atualmente suporta "bank_statement")
- `file_content`: Conteúdo do arquivo em Base64
- `content_type`: MIME type do arquivo (application/pdf, image/jpeg, etc.)
- `categories`: Lista opcional de categorias predefinidas

### Configurações Disponíveis

Principais variáveis de ambiente:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão com o banco de dados | postgresql://postgres:postgres@localhost:5432/financial_docs |
| `KAFKA_BOOTSTRAP_SERVERS` | Servidores Kafka | localhost:9092 |
| `KAFKA_DOCUMENTS_TOPIC` | Tópico para recebimento de documentos | documents-to-process |
| `KAFKA_PROCESSED_TOPIC` | Tópico para documentos processados | processed-documents |
| `AI_PROVIDER` | Provedor de IA (openai, gemini, claude) | openai |
| `OPENAI_API_KEY` | Chave de API da OpenAI | - |
| `OPENAI_MODEL` | Modelo da OpenAI | gpt-4o |
| `GEMINI_API_KEY` | Chave de API do Gemini | - |
| `GEMINI_MODEL` | Modelo do Gemini | gemini-1.5-pro |
| `ANTHROPIC_API_KEY` | Chave de API da Anthropic | - |
| `CLAUDE_MODEL` | Modelo do Claude | claude-3-opus-20240229 |
| `LOG_LEVEL` | Nível de log | INFO |

## 📊 Fluxo de Processamento

1. **Recebimento**: Documento é recebido via Kafka
2. **Decodificação**: Conteúdo em Base64 é decodificado e texto é extraído 
3. **Extração**: IA extrai transações do texto, identificando datas, valores, etc.
4. **Categorização**: Transações são categorizadas pela IA
5. **Persistência**: Transações são salvas no banco de dados
6. **Notificação**: Mensagem de confirmação é enviada via Kafka

## 🔄 Adaptadores de IA

O sistema suporta três provedores de IA:

### OpenAI

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o  # Ou gpt-3.5-turbo para menor custo
```

### Google Gemini

```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-1.5-pro  # Ou gemini-1.5-flash para menor custo
```

### Anthropic Claude

```bash
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sua_chave_aqui
CLAUDE_MODEL=claude-3-opus-20240229  # Ou claude-3-haiku-20240307 para menor custo
```

## 📉 Estratégias de Otimização de Custos

1. **Processamento em Lotes**: Transações são agrupadas para reduzir chamadas de API
2. **Templates de Prompts Otimizados**: Prompts específicos para cada provedor
3. **Fallback Inteligente**: Usa modelos mais baratos quando possível
4. **Caching**: Evita reprocessamento de padrões comuns

## 🔍 Monitoramento e Observabilidade

O serviço expõe várias métricas Prometheus para monitoramento:

- `document_processed_total`: Contador de documentos processados (por tipo e status)
- `transaction_extracted_total`: Contador de transações extraídas (por tipo de documento)
- `document_processing_seconds`: Histograma de tempo de processamento
- `ai_api_calls_total`: Contador de chamadas de API de IA
- `ai_token_usage_total`: Contador de tokens consumidos
- `ai_cost_usd_total`: Contador de custos estimados em USD

Métricas podem ser acessadas em `http://localhost:8000/` quando o serviço está em execução.

### Logs Estruturados

Os logs são estruturados e incluem informações detalhadas sobre cada etapa do processamento:

```
2023-05-10 14:35:22 | INFO     | financial_document_processor.main:handle_document:215 - Processando documento 12345 do tipo bank_statement
2023-05-10 14:35:25 | INFO     | financial_document_processor.services.document_processor:process:89 - Processamento do documento 12345 concluído em 3.21s. Extraídas 15 transações.
```

## 🗄️ Banco de Dados e Migrações

O projeto utiliza SQLAlchemy e Alembic para gerenciar o esquema do banco de dados. As migrações estão localizadas no diretório `migrations/`.

### Executando Migrações

Para configurar o banco de dados pela primeira vez:

```bash
# Aplicar todas as migrações
python scripts/db_migrate.py upgrade
```

### Gerenciando Migrações

Para criar uma nova migração após alterar modelos:

```bash
# Cria uma nova migração com base nas alterações nos modelos
python scripts/db_migrate.py create "Descrição da migração"
```

Para reverter a última migração:

```bash
# Reverte a última migração aplicada
python scripts/db_migrate.py downgrade
```

Consulte `migrations/README.md` para mais detalhes sobre o sistema de migrações.

## 🔄 Categorização de Transações

O sistema utiliza uma combinação de regras e IA para categorizar transações em categorias como:

- Moradia (aluguel, luz, água, internet)
- Alimentação (supermercado, restaurantes)
- Transporte (combustível, transporte público)
- Saúde (plano de saúde, farmácia)
- Educação (mensalidades, cursos)
- Lazer (viagens, entretenimento)

## 🔧 Testes

Execute os testes com:

```bash
# Testes unitários
pytest tests/unit

# Testes de integração
pytest tests/integration

# Verificar cobertura
pytest --cov=financial_document_processor
```

## 📝 Exemplos de Uso

### Enviando um documento para processamento via Kafka

```python
import base64
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

# Configurar o produtor Kafka
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Ler o arquivo e codificar em base64
with open('extrato.pdf', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')

# Criar o payload
document = {
    "id": 12345,
    "external_id": str(uuid.uuid4()),
    "user_id": 98765,
    "document_type": "bank_statement",
    "filename": "extrato.pdf",
    "content_type": "application/pdf",
    "file_content": file_content,
    "categories": ["moradia", "alimentação", "transporte"],
    "status": "pending",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

# Enviar para o Kafka
producer.send('documents-to-process', document)
producer.flush()
print("Documento enviado para processamento!")
```

### Consumindo resultados do processamento

```python
import json
from kafka import KafkaConsumer

# Configurar o consumidor Kafka
consumer = KafkaConsumer(
    'processed-documents',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    group_id='result-consumer',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Consumir mensagens
for message in consumer:
    result = message.value
    print(f"Documento {result['document_id']} processado:")
    print(f"- Status: {result['status']}")
    print(f"- Transações: {result.get('transaction_count', 0)}")
    
    if result['status'] == 'FAILED':
        print(f"- Erro: {result.get('error', 'Desconhecido')}")
```

## 📋 Roadmap

- [x] Processamento de extratos bancários
- [ ] Suporte para notas fiscais
- [ ] Suporte para fatura de cartão de crédito
- [ ] API REST para consulta de transações
- [ ] Dashboards de visualização
- [ ] Exportação para sistemas contábeis
- [ ] Melhorias no modelo de categorização
- [ ] Detecção de fraudes e anomalias

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📜 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## 📞 Suporte

Para problemas, dúvidas ou sugestões, por favor abra uma issue no GitHub ou entre em contato pelo email [seu.email@exemplo.com](mailto:seu.email@exemplo.com).

---

Feito com ❤️ para tornar o processamento de documentos financeiros mais eficiente e inteligente.