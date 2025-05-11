"""
Configuração e fixtures para testes automatizados.
"""
import asyncio
import base64
import json
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from financial_document_processor.adapters.ai.ai_provider import AIProvider, AIResponse
from financial_document_processor.adapters.database.models import Base
from financial_document_processor.domain.document import Document
from financial_document_processor.domain.transaction import Transaction, TransactionType, TransactionMethod


# Configuração do banco de dados de teste
@pytest.fixture(scope="session")
def test_db_url():
    """URL para o banco de dados de teste."""
    return "postgresql://postgres:0879@localhost:5432/financial_docs_test"


@pytest.fixture(scope="session")
def engine(test_db_url):
    """Cria uma engine SQLAlchemy para os testes."""
    engine = create_engine(test_db_url)
    return engine


@pytest.fixture(scope="session")
def setup_test_db(engine, test_db_url):
    """Configura o banco de dados de teste."""
    # Cria o banco de dados de teste se não existir
    default_db_url = re.sub(r'/financial_docs_test$', '/postgres', test_db_url)
    temp_engine = create_engine(default_db_url)

    with temp_engine.connect() as conn:
        # Desconecta possíveis sessões ativas
        conn.execute(
            text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'financial_docs_test'"))
        conn.execute(text("COMMIT"))

        # Drop e recria o banco de dados
        conn.execute(text("DROP DATABASE IF EXISTS financial_docs_test"))
        conn.execute(text("CREATE DATABASE financial_docs_test"))

    # Cria as tabelas no banco de teste
    with engine.begin() as conn:
        Base.metadata.create_all(conn)

    # Permite que alembic_version seja dropada durante os testes
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))

    yield

    # Limpa o banco de dados após os testes
    with engine.begin() as conn:
        Base.metadata.drop_all(conn)


@pytest.fixture
def async_session_factory(setup_test_db, test_db_url):
    """Cria uma fábrica de sessões assíncronas."""
    async_engine = create_async_engine(test_db_url.replace('postgresql://', 'postgresql+asyncpg://'))
    async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    return async_session


@pytest.fixture
async def async_session(async_session_factory):
    """Cria uma sessão assíncrona para os testes."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# Mock do provedor de IA para testes
class MockAIProvider(AIProvider):
    """Implementação de um provedor de IA para testes."""

    def __init__(self, transactions=None):
        """
        Inicializa o mock com transações predefinidas.

        Args:
            transactions: Lista de transações a serem retornadas (opcional)
        """
        self.transactions = transactions or []
        self.call_count = 0

    @property
    def name(self) -> str:
        return "MockAI"

    def get_cost_per_1k_tokens(self) -> float:
        return 0.001

    async def generate_completion(self, request):
        """Mock para gerar uma resposta de IA."""
        self.call_count += 1
        return AIResponse(
            content=json.dumps({"transactions": [t.model_dump() for t in self.transactions]}),
            model="mock-model",
            tokens_used=100,
            cost=0.0001
        )

    async def extract_transactions(self, text_content, document_type, predefined_categories=None, document_id=1, user_id=1):
        """Mock para extrair transações."""
        self.call_count += 1
        for transaction in self.transactions:
            transaction.user_id = user_id
            transaction.document_id = document_id
        return self.transactions

    async def categorize_transactions(self, transactions, predefined_categories=None):
        """Mock para categorizar transações."""
        self.call_count += 1

        # Se não houver transações, retorna uma lista vazia
        if not transactions:
            return []

        # Se não há transações predefinidas, apenas adiciona categorias às fornecidas
        if not self.transactions:
            for tx in transactions:
                if not tx.categories or len(tx.categories) == 0:
                    tx.categories = ["categoria_teste"]
                tx.confidence_score = 0.95
            return transactions

        # Caso contrário, retorna as transações predefinidas
        return self.transactions


@pytest.fixture
def mock_ai_provider():
    """Cria um mock do provedor de IA."""
    transactions = [
        Transaction(
            id=uuid.uuid4(),
            document_id=1,
            user_id=123,
            date=datetime.now().date(),
            description="TRANSFERÊNCIA RECEBIDA - TESTE",
            amount=Decimal(1000.00),
            type=TransactionType.CREDIT,
            method=TransactionMethod.PIX,
            categories=["salário"],
            confidence_score=0.95
        ),
        Transaction(
            id=uuid.uuid4(),
            document_id=1,
            user_id=123,
            date=datetime.now().date(),
            description="PAGAMENTO - CONTA DE LUZ",
            amount=Decimal(150.25),
            type=TransactionType.DEBIT,
            method=TransactionMethod.BOLETO,
            categories=["utilidades", "conta de luz"],
            confidence_score=0.92
        )
    ]

    return MockAIProvider(transactions)


# Fixtures para documentos de teste
@pytest.fixture
def sample_document_dict():
    """Cria um dicionário representando um documento de teste."""
    current_dir = Path(__file__).parent
    fixture_path = current_dir / "fixtures" / "sample_bank_statement.txt"

    # Se o arquivo de fixture não existir, cria um texto de exemplo
    if not fixture_path.exists():
        fixture_path.parent.mkdir(exist_ok=True)
        with open(fixture_path, "w") as f:
            f.write("Este é um exemplo de extrato bancário para teste.")

    # Lê o conteúdo do arquivo e codifica em base64
    with open(fixture_path, "rb") as f:
        file_content = base64.b64encode(f.read()).decode("utf-8")

    # Cria um documento de teste
    return {
        "id": 12345,
        "external_id": str(uuid.uuid4()),
        "user_id": 98765,
        "document_type": "bank_statement",
        "filename": "extrato_teste.txt",
        "content_type": "text/plain",
        "file_content": file_content,
        "categories": ["salário", "utilidades"],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
    }


@pytest.fixture
def sample_document(sample_document_dict):
    """Cria um objeto Document de teste."""
    return Document(**sample_document_dict)


# Configura o pytest para executar testes assíncronos
@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para os testes assíncronos."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


class MockConnection:
    """Mock de conexão que simplesmente passa as operações para a sessão."""

    def __init__(self, session):
        self.session = session

    async def fetchrow(self, query, *args, **kwargs):
        """Simula fetchrow usando execute da sessão."""
        result = await self.session.execute(query, *args, **kwargs)
        row = result.fetchone()
        return row  # Isso retorna um objeto Row, que é similar ao que fetchrow retornaria

    async def fetch(self, query, *args, **kwargs):
        """Simula fetch usando execute da sessão."""
        result = await self.session.execute(query, *args, **kwargs)
        rows = result.fetchall()
        return rows

    async def execute(self, query, *args, **kwargs):
        """Executa a query na sessão."""
        result = await self.session.execute(query, *args, **kwargs)
        return result

    # Outros métodos que seu PostgresRepository pode usar
    # Por exemplo, se você usa transações:
    async def begin(self):
        """Inicia uma transação."""
        return self

    async def __aenter__(self):
        """Suporte para 'async with'."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Suporte para 'async with'."""
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()


@pytest.fixture
def mock_postgres_pool(async_session):
    """
    Cria um mock do pool de conexões PostgreSQL.

    Este mock simula o comportamento de um pool asyncpg, mas redireciona
    chamadas para a sessão SQLAlchemy fornecida pelo fixture async_session.
    """
    mock_pool = MagicMock()

    # Cria um mock para o método acquire
    async def mock_acquire():
        connection = MockConnection(async_session)
        return connection

    # Configura o mock_pool.acquire para retornar um AsyncContextManager
    mock_acquire_context = AsyncMock()
    mock_acquire_context.__aenter__.side_effect = mock_acquire
    mock_pool.acquire.return_value = mock_acquire_context

    return mock_pool


@pytest.fixture
async def postgres_repo(mock_postgres_pool):
    """
    Cria um repositório PostgreSQL para testes.

    Utiliza um pool mockado para redirecionar operações para a sessão SQLAlchemy.
    """
    from financial_document_processor.adapters.database.postgres import PostgresRepository

    repo = PostgresRepository(connection_string="")
    repo.pool = mock_postgres_pool

    return repo