"""
Testes unitários para os adaptadores de IA.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from financial_document_processor.adapters.ai import create_ai_provider
from financial_document_processor.adapters.ai.ai_provider import AIRequest
from financial_document_processor.domain.transaction import Transaction, TransactionType


@pytest.mark.asyncio
async def test_mock_ai_provider_extract_transactions(mock_ai_provider):
    """Testa a extração de transações usando o mock de provedor de IA."""
    # Texto de exemplo para análise
    text_content = "Este é um exemplo de extrato bancário para teste."

    # Extrai transações usando o mock
    transactions = await mock_ai_provider.extract_transactions(
        text_content=text_content,
        document_type="bank_statement"
    )

    # Verifica se o resultado é uma lista de transações
    assert isinstance(transactions, list)
    assert len(transactions) > 0
    assert all(isinstance(tx, Transaction) for tx in transactions)

    # Verifica se o mock foi chamado
    assert mock_ai_provider.call_count == 1


@pytest.mark.asyncio
async def test_mock_ai_provider_categorize_transactions(mock_ai_provider):
    """Testa a categorização de transações usando o mock de provedor de IA."""
    # Cria uma transação de exemplo sem categorias
    transaction = Transaction(
        id=uuid4(),
        document_id=1,
        user_id=123,
        date=datetime.now().date(),
        description="COMPRA NO MERCADO",
        amount=Decimal("50.00"),
        type=TransactionType.DEBIT
    )

    # Categoriza a transação usando o mock
    categorized = await mock_ai_provider.categorize_transactions(
        transactions=[transaction]
    )

    # Verifica se a transação foi categorizada
    assert isinstance(categorized, list)
    assert len(categorized) > 0
    assert all(len(tx.categories) > 0 for tx in categorized)

    # Verifica se o mock foi chamado
    assert mock_ai_provider.call_count == 1


@pytest.mark.asyncio
async def test_mock_ai_provider_completion(mock_ai_provider):
    """Testa a geração de completions usando o mock de provedor de IA."""
    # Cria uma requisição de exemplo
    request = AIRequest(
        prompt="Extraia transações deste texto: PAGAMENTO CONTA DE LUZ R$ 150,00",
        temperature=0.0
    )

    # Gera uma completion usando o mock
    response = await mock_ai_provider.generate_completion(request)

    # Verifica a resposta
    assert response is not None
    assert response.content is not None
    assert response.model == "mock-model"
    assert response.tokens_used == 100
    assert response.cost == 0.0001

    # Verifica se o mock foi chamado
    assert mock_ai_provider.call_count == 1


@pytest.mark.asyncio
async def test_mock_ai_provider_empty_transactions(mock_ai_provider):
    """Testa o comportamento com lista vazia de transações."""
    # Tenta categorizar uma lista vazia
    categorized = await mock_ai_provider.categorize_transactions([])

    # Verifica se o resultado é uma lista vazia
    assert isinstance(categorized, list)
    assert len(categorized) == 0

    # Verifica se o mock foi chamado
    assert mock_ai_provider.call_count == 1


@pytest.mark.asyncio
async def test_create_ai_provider():
    """Testa a fábrica de provedores de IA."""
    # Isso apenas verifica se a função não lança exceções
    # Em um ambiente real, você usaria mocks para as APIs externas

    # Testa se a função levanta a exceção esperada para provedor inválido
    with pytest.raises(ValueError, match="Provedor não suportado"):
        create_ai_provider("invalid_provider", "fake_api_key")