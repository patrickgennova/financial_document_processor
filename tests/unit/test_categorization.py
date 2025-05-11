"""
Testes unitários para o serviço de categorização.
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from financial_document_processor.domain.transaction import Transaction, TransactionType
from financial_document_processor.services.categorization import CategorizationService


@pytest.fixture
def sample_transaction():
    """Cria uma transação de exemplo para testes."""
    return Transaction(
        id=uuid4(),
        document_id=1,
        user_id=123,
        date=date.today(),
        description="PAGAMENTO CONTA DE LUZ",
        amount=Decimal("150.25"),
        type=TransactionType.DEBIT,
        categories=[]
    )


@pytest.fixture
def mock_ai_provider():
    """Cria um mock do provedor de IA para o serviço de categorização."""
    provider = MagicMock()
    provider.categorize_transactions = AsyncMock()
    return provider


@pytest.fixture
def categorization_service(mock_ai_provider):
    """Cria uma instância do serviço de categorização."""
    return CategorizationService(
        ai_provider=mock_ai_provider,
        predefined_categories=["luz", "água", "internet", "aluguel", "salário"],
        batch_size=2,
        enable_caching=True
    )


@pytest.mark.asyncio
async def test_categorize_transaction_rule_based(categorization_service, sample_transaction):
    """Testa a categorização baseada em regras."""
    # Categoriza a transação
    categorized = await categorization_service.categorize_transaction(sample_transaction, use_ai=False)

    # Verifica se as categorias foram aplicadas
    assert categorized.categories is not None
    assert len(categorized.categories) > 0

    # Verifica se a categoria "luz" está presente (deve ser detectada pela regra)
    assert any(cat for cat in categorized.categories if "luz" in cat.lower())

    # Verifica se a pontuação de confiança foi definida
    assert categorized.confidence_score is not None
    assert 0 <= categorized.confidence_score <= 1


@pytest.mark.asyncio
async def test_categorize_transaction_with_ai(categorization_service, sample_transaction, mock_ai_provider):
    """Testa a categorização usando IA."""
    # Configura o mock do provedor de IA
    mock_transaction = sample_transaction.model_copy()
    mock_transaction.categories = ["luz"]
    mock_transaction.confidence_score = 0.9
    mock_ai_provider.categorize_transactions.return_value = [mock_transaction]

    # Categoriza a transação
    categorized = await categorization_service.categorize_transaction(sample_transaction, use_ai=True)

    # Verifica se o provedor de IA foi chamado
    mock_ai_provider.categorize_transactions.assert_called_once()

    # Verifica se as categorias foram aplicadas
    assert categorized.categories == ["luz"]
    assert categorized.confidence_score == 0.9


@pytest.mark.asyncio
async def test_categorize_multiple_transactions(categorization_service, mock_ai_provider):
    """Testa a categorização de múltiplas transações."""
    # Cria algumas transações de teste
    transactions = [
        Transaction(
            id=uuid4(),
            document_id=1,
            user_id=123,
            date=date.today(),
            description="PAGAMENTO CONTA DE LUZ",
            amount=Decimal("150.25"),
            type=TransactionType.DEBIT,
            categories=[]
        ),
        Transaction(
            id=uuid4(),
            document_id=1,
            user_id=123,
            date=date.today(),
            description="TRANSFERÊNCIA RECEBIDA",
            amount=Decimal("3000.00"),
            type=TransactionType.CREDIT,
            categories=[]
        )
    ]

    # Configura o mock do provedor de IA
    categorized_transactions = []
    for tx in transactions:
        tx_copy = tx.model_copy()
        tx_copy.categories = ["categoria_mock"]
        tx_copy.confidence_score = 0.85
        categorized_transactions.append(tx_copy)

    mock_ai_provider.categorize_transactions.return_value = categorized_transactions

    # Categoriza as transações
    result = await categorization_service.categorize_transactions(transactions)

    # Verifica se o resultado é uma lista de transações
    assert isinstance(result, list)
    assert len(result) == len(transactions)

    # Verifica se todas as transações foram categorizadas
    assert all(len(tx.categories) > 0 for tx in result)

    # Verifica o número de chamadas ao provedor de IA
    # Deve ser 1 porque o batch_size é 2 e temos 2 transações
    assert mock_ai_provider.categorize_transactions.call_count == 1


@pytest.mark.asyncio
async def test_cache_functionality(categorization_service, sample_transaction, mock_ai_provider):
    """Testa a funcionalidade de cache do serviço de categorização."""
    # Configura o mock do provedor de IA
    mock_transaction = sample_transaction.model_copy()
    mock_transaction.categories = ["luz"]
    mock_transaction.confidence_score = 0.9
    mock_ai_provider.categorize_transactions.return_value = [mock_transaction]

    # Primeira chamada - deve usar IA
    await categorization_service.categorize_transaction(sample_transaction, use_ai=True)

    # Segunda chamada com transação similar - deve usar cache
    similar_transaction = sample_transaction.model_copy()
    similar_transaction.id = uuid4()  # ID diferente, mas descrição similar

    await categorization_service.categorize_transaction(similar_transaction, use_ai=True)

    # Verifica se o provedor de IA foi chamado apenas uma vez
    assert mock_ai_provider.categorize_transactions.call_count == 1


@pytest.mark.asyncio
async def test_filter_categories(categorization_service):
    """Testa a filtragem de categorias com base em lista permitida."""
    # Lista de categorias para filtrar
    categories = ["luz", "água", "categoria_inexistente"]

    # Filtra as categorias
    filtered = categorization_service.filter_categories(
        categories, allowed_categories=["luz", "internet", "aluguel"]
    )

    # Verifica se apenas categorias permitidas foram mantidas
    assert "luz" in filtered
    assert "água" not in filtered
    assert "categoria_inexistente" not in filtered


@pytest.mark.asyncio
async def test_rule_based_categorization_debit(categorization_service):
    """Testa a categorização baseada em regras para transações de débito."""
    # Cria uma transação de débito
    transaction = Transaction(
        id=uuid4(),
        document_id=1,
        user_id=123,
        date=date.today(),
        description="SUPERMERCADO EXTRA",
        amount=Decimal("253.45"),
        type=TransactionType.DEBIT,
        categories=[]
    )

    # Categoriza a transação usando regras
    categories, confidence = categorization_service._rule_based_categorization(transaction)

    # Verifica se alguma categoria foi atribuída
    assert len(categories) > 0

    # Verifica a pontuação de confiança
    assert 0 <= confidence <= 1


@pytest.mark.asyncio
async def test_rule_based_categorization_credit(categorization_service):
    """Testa a categorização baseada em regras para transações de crédito."""
    # Cria uma transação de crédito
    transaction = Transaction(
        id=uuid4(),
        document_id=1,
        user_id=123,
        date=date.today(),
        description="TRANSFERÊNCIA RECEBIDA - SALÁRIO",
        amount=Decimal("3000.00"),
        type=TransactionType.CREDIT,
        categories=[]
    )

    # Categoriza a transação usando regras
    categories, confidence = categorization_service._rule_based_categorization(transaction)

    # Verifica se alguma categoria foi atribuída
    assert len(categories) > 0
    assert "salário" in categories

    # Verifica a pontuação de confiança
    assert 0 <= confidence <= 1


@pytest.mark.asyncio
async def test_generate_cache_key(categorization_service):
    """Testa a geração de chave de cache."""
    # Cria duas transações com diferente descritivo mas padrão similar
    transaction1 = Transaction(
        id=uuid4(),
        document_id=1,
        user_id=123,
        date=date.today(),
        description="NETFLIX STREAMING 29.90",
        amount=Decimal("29.90"),
        type=TransactionType.DEBIT,
        categories=[]
    )

    transaction2 = Transaction(
        id=uuid4(),
        document_id=1,
        user_id=456,
        date=date.today(),
        description="NETFLIX STREAMING 39.90",
        amount=Decimal("39.90"),
        type=TransactionType.DEBIT,
        categories=[]
    )

    # Gera chaves de cache
    key1 = categorization_service._generate_cache_key(transaction1)
    key2 = categorization_service._generate_cache_key(transaction2)

    # Verifica se as chaves são iguais (ignorando números)
    assert key1 == key2