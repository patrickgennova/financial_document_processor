from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from financial_document_processor.config import get_settings

# Este é o arquivo de configuração do Alembic
config = context.config

# Sobrescreve a URL de conexão com a do arquivo .env
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.url)

# Configura logging via arquivo de configuração do Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importa o modelo de metadados para operações de autogeneração
from financial_document_processor.adapters.database.models import Base
target_metadata = Base.metadata

def run_migrations_offline():
    """Executa migrações em modo 'offline'.

    Isso configura o contexto com apenas uma URL
    e não um Engine, embora um Engine seja aceito
    em nosso context.configure também.

    Assim, as migrações podem ser conduzidas via conexão existente
    ou apenas geradas como SQL para execução posterior.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Executa migrações em modo 'online'.

    Neste cenário, precisamos criar um Engine
    e associá-lo a um contexto.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()