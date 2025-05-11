# Financial Document Processor

[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An efficient microservice for processing financial documents using Artificial Intelligence.

## 📋 Overview

Financial Document Processor is a Python microservice that:

1. Consumes Kafka messages containing financial documents (in base64)
2. Decodes and extracts text from these documents (bank statements, etc.)
3. Uses AI to extract transactions and categorize them with high precision
4. Persists the results and notifies downstream systems via Kafka

Its main features include:

- **Pluggable AI Architecture**: Easily switch between OpenAI, Gemini, and Claude
- **High Performance**: Efficient processing optimized for cost
- **Security and Reliability**: Robust design for confidential financial data
- **Scalability**: Fully asynchronous architecture ready for horizontal scaling
- **Observability**: Detailed logging and Prometheus metrics

## 🏗️ Architecture

This project follows the principles of Hexagonal Architecture (Ports & Adapters):

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

## 🚀 Installation Instructions

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Access to a Kafka cluster
- API credentials for AI providers (OpenAI, Gemini, Claude)

### Installation with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/financial-document-processor.git
   cd financial-document-processor
   ```

2. Configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit the .env file with your credentials
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/financial-document-processor.git
   cd financial-document-processor
   ```

2. Set up the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit the .env file with your credentials
   ```

5. Run the service:
   ```bash
   python -m financial_document_processor.main
   ```

## 📝 Usage and Configuration

### Kafka Message Format

The service expects messages in the following JSON format:

```json
{
  "id": 12345,
  "external_id": "44f437b5-a093-4a53-bc59-dd427f8e9c56",
  "user_id": 98765,
  "document_type": "bank_statement",
  "filename": "statement-may-2023.pdf",
  "content_type": "application/pdf",
  "file_content": "base64_encoded_string_here...",
  "categories": ["category1", "category2"],
  "status": "pending",
  "created_at": "2023-05-10T14:30:00Z",
  "updated_at": "2023-05-10T14:30:00Z"
}
```

Important fields:
- `document_type`: Document type (currently supports "bank_statement")
- `file_content`: File content in Base64
- `content_type`: File MIME type (application/pdf, image/jpeg, etc.)
- `categories`: Optional list of predefined categories

### Available Configurations

Main environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | postgresql://postgres:postgres@localhost:5432/financial_docs |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka servers | localhost:9092 |
| `KAFKA_DOCUMENTS_TOPIC` | Topic for receiving documents | documents-to-process |
| `KAFKA_PROCESSED_TOPIC` | Topic for processed documents | processed-documents |
| `AI_PROVIDER` | AI provider (openai, gemini, claude) | openai |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | gpt-4o |
| `GEMINI_API_KEY` | Gemini API key | - |
| `GEMINI_MODEL` | Gemini model | gemini-1.5-pro |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `CLAUDE_MODEL` | Claude model | claude-3-opus-20240229 |
| `LOG_LEVEL` | Log level | INFO |

## 📊 Processing Flow

1. **Receipt**: Document is received via Kafka
2. **Decoding**: Base64 content is decoded and text is extracted
3. **Extraction**: AI extracts transactions from the text, identifying dates, values, etc.
4. **Categorization**: Transactions are categorized by the AI
5. **Persistence**: Transactions are saved to the database
6. **Notification**: Confirmation message is sent via Kafka

## 🔄 AI Adapters

The system supports three AI providers:

### OpenAI

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o  # Or gpt-3.5-turbo for lower cost
```

### Google Gemini

```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-pro  # Or gemini-1.5-flash for lower cost
```

### Anthropic Claude

```bash
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-3-opus-20240229  # Or claude-3-haiku-20240307 for lower cost
```

## 📉 Cost Optimization Strategies

1. **Batch Processing**: Transactions are grouped to reduce API calls
2. **Optimized Prompt Templates**: Provider-specific prompts
3. **Intelligent Fallback**: Uses cheaper models when possible
4. **Caching**: Avoids reprocessing common patterns

## 🔍 Monitoring and Observability

The service exposes various Prometheus metrics for monitoring:

- `document_processed_total`: Counter of processed documents (by type and status)
- `transaction_extracted_total`: Counter of extracted transactions (by document type)
- `document_processing_seconds`: Processing time histogram
- `ai_api_calls_total`: Counter of AI API calls
- `ai_token_usage_total`: Counter of tokens consumed
- `ai_cost_usd_total`: Counter of estimated costs in USD

Metrics can be accessed at `http://localhost:8000/` when the service is running.

### Structured Logs

Logs are structured and include detailed information about each processing step:

```
2023-05-10 14:35:22 | INFO     | financial_document_processor.main:handle_document:215 - Processing document 12345 of type bank_statement
2023-05-10 14:35:25 | INFO     | financial_document_processor.services.document_processor:process:89 - Document 12345 processing completed in 3.21s. Extracted 15 transactions.
```

## 🗄️ Database and Migrations

The project uses SQLAlchemy and Alembic to manage the database schema. Migrations are located in the `migrations/` directory.

### Running Migrations

To configure the database for the first time:

```bash
# Apply all migrations
python scripts/db_migrate.py upgrade
```

### Managing Migrations

To create a new migration after changing models:

```bash
# Create a new migration based on model changes
python scripts/db_migrate.py create "Migration description"
```

To revert the last migration:

```bash
# Revert the last applied migration
python scripts/db_migrate.py downgrade
```

See `migrations/README.md` for more details about the migration system.

## 🔄 Transaction Categorization

The system uses a combination of rules and AI to categorize transactions into categories such as:

- Housing (rent, utilities, water, internet)
- Food (supermarket, restaurants)
- Transportation (fuel, public transport)
- Health (health insurance, pharmacy)
- Education (tuition, courses)
- Leisure (travel, entertainment)

## 🔧 Tests

Run the tests with:

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Check coverage
pytest --cov=financial_document_processor
```

## 📝 Usage Examples

### Sending a document for processing via Kafka

```python
import base64
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

# Configure the Kafka producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Read the file and encode in base64
with open('statement.pdf', 'rb') as f:
    file_content = base64.b64encode(f.read()).decode('utf-8')

# Create the payload
document = {
    "id": 12345,
    "external_id": str(uuid.uuid4()),
    "user_id": 98765,
    "document_type": "bank_statement",
    "filename": "statement.pdf",
    "content_type": "application/pdf",
    "file_content": file_content,
    "categories": ["housing", "food", "transport"],
    "status": "pending",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

# Send to Kafka
producer.send('documents-to-process', document)
producer.flush()
print("Document sent for processing!")
```

### Consuming processing results

```python
import json
from kafka import KafkaConsumer

# Configure the Kafka consumer
consumer = KafkaConsumer(
    'processed-documents',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    group_id='result-consumer',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Consume messages
for message in consumer:
    result = message.value
    print(f"Document {result['document_id']} processed:")
    print(f"- Status: {result['status']}")
    print(f"- Transactions: {result.get('transaction_count', 0)}")
    
    if result['status'] == 'FAILED':
        print(f"- Error: {result.get('error', 'Unknown')}")
```

## 📋 Roadmap

- [x] Bank statement processing
- [ ] Invoice support
- [ ] Credit card statement support
- [ ] REST API for transaction queries
- [ ] Visualization dashboards
- [ ] Export to accounting systems
- [ ] Improvements to the categorization model
- [ ] Fraud and anomaly detection

## 🤝 Contributing

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the [MIT License](LICENSE).

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub or contact via email at [your.email@example.com](mailto:your.email@example.com).

---

Made with ❤️ to make financial document processing more efficient and intelligent.