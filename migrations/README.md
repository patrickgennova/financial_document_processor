# Migrações de Banco de Dados

Este diretório contém as migrações de banco de dados para o Financial Document Processor.
As migrações são gerenciadas usando o Alembic.

## Estrutura

- `versions/`: Diretório contendo os scripts de migração
- `env.py`: Configuração do ambiente de migração
- `script.py.mako`: Template para geração de novos scripts de migração

## Como usar

### Instalar dependências

```bash
pip install alembic sqlalchemy psycopg2-binary
```

### Executar migrações

Para aplicar todas as migrações pendentes:

```bash
python scripts/db_migrate.py upgrade
```

Para reverter a última migração:

```bash
python scripts/db_migrate.py downgrade
```

### Criar uma nova migração

Para criar uma nova migração manualmente:

```bash
python scripts/db_migrate.py create "Descrição da migração"
```

Este comando criará um novo arquivo de migração em `migrations/versions/`.

### Comandos Alembic diretos

Você também pode usar os comandos do Alembic diretamente:

```bash
# Ver migração atual
alembic current

# Ver histórico de revisões
alembic history

# Aplicar migrations específicas
alembic upgrade +2  # Aplica as próximas duas migrações
alembic upgrade revision_id  # Aplica até uma revisão específica

# Reverter migrations
alembic downgrade -1  # Reverte a última migração
alembic downgrade revision_id  # Reverte até uma revisão específica
```

## Convenções

1. Mantenha scripts de migração idempotentes (podem ser aplicados várias vezes sem efeitos colaterais)
2. Cada migração deve fazer apenas uma alteração lógica no esquema
3. Scripts de migração devem ter nomes descritivos
4. Prefixe o nome dos arquivos com números sequenciais para facilitar a ordenação

## Observações

- O banco de dados PostgreSQL é necessário
- As migrações são testadas apenas com PostgreSQL
- A URL de conexão é obtida automaticamente do arquivo `.env`