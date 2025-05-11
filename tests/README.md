# Testes Automatizados

Este diretório contém os testes automatizados para o Financial Document Processor. Os testes são organizados em duas categorias principais:

1. **Testes Unitários** (`tests/unit`): Testam componentes individuais de forma isolada
2. **Testes de Integração** (`tests/integration`): Testam a interação entre múltiplos componentes

## Estrutura de Diretórios

```
tests/
├── conftest.py          # Configurações e fixtures compartilhadas
├── fixtures/            # Arquivos de exemplo para testes
│   └── sample_bank_statement.txt
├── integration/         # Testes de integração
│   ├── test_document_flow.py
│   ├── test_kafka.py
│   └── test_repository.py
└── unit/               # Testes unitários
    ├── test_ai_provider.py
    ├── test_categorization.py
    ├── test_document_processor.py
    ├── test_file_decoder.py
    └── test_prompt_engineering.py
```

## Executando os Testes

### Usando o script de execução

Para maior conveniência, utilize o script `run_tests.py`:

```bash
# Executar todos os testes
python scripts/run_tests.py all

# Executar apenas testes unitários
python scripts/run_tests.py unit

# Executar apenas testes de integração
python scripts/run_tests.py integration

# Executar com relatório de cobertura
python scripts/run_tests.py all --coverage
```

### Usando pytest diretamente

Também é possível executar os testes diretamente com o `pytest`:

```bash
# Executar todos os testes
pytest

# Executar testes específicos
pytest tests/unit/
pytest tests/integration/

# Executar com cobertura
pytest --cov=financial_document_processor

# Executar um arquivo de teste específico
pytest tests/unit/test_file_decoder.py
```

## Fixtures e Mocks

O arquivo `conftest.py` contém fixtures e mocks compartilhados para os testes:

- **setup_test_db**: Configura o banco de dados de teste
- **async_session**: Fornece uma sessão de banco de dados para testes
- **mock_ai_provider**: Mock do provedor de IA para testes
- **sample_document_dict**: Dados de exemplo para um documento
- **sample_document**: Objeto Document de exemplo

## Testes de Integração

Os testes de integração requerem um banco de dados PostgreSQL local. Antes de executar, certifique-se de que:

1. O PostgreSQL está em execução
2. Existe um usuário `postgres` com senha `postgres`
3. O usuário tem permissão para criar bancos de dados

O teste criará um banco de dados temporário chamado `financial_docs_test`.

## Relatório de Cobertura

Para gerar um relatório de cobertura de testes:

```bash
python scripts/run_tests.py all --coverage
```

O relatório HTML será gerado em `htmlcov/index.html`.