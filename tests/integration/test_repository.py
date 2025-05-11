"""
Testes de integração para o repositório de banco de dados.
"""
import pytest
import uuid
from datetime import datetime
from decimal import Decimal

from financial_document_processor.domain.document import Document, DocumentStatus
from financial_document_processor.domain.transaction import Transaction, TransactionType


@pytest.mark.asyncio
async def test_save_document(postgres_repo, sample_document_dict):
    """Testa salvar um documento no banco de dados."""
    # Cria o repositório
    repo = postgres_repo

    # Cria um documento de teste
    document = Document(**sample_document_dict)

    # Salva o documento
    saved_document = await repo.save_document(document)

    # Verifica se o documento foi salvo corretamente
    assert saved_document.id == document.id

    # Recupera o documento do banco
    retrieved_document = await repo.get_document(document.id)

    # Verifica se o documento recuperado é igual ao original
    assert retrieved_document is not None
    assert retrieved_document.id == document.id
    assert retrieved_document.external_id == document.external_id
    assert retrieved_document.user_id == document.user_id
    assert retrieved_document.document_type == document.document_type
    assert retrieved_document.status == document.status


@pytest.mark.asyncio
async def test_update_document_status(postgres_repo, sample_document_dict):
    """Testa atualizar o status de um documento."""
    # Cria o repositório
    repo = postgres_repo

    # Cria e salva um documento
    document = Document(**sample_document_dict)
    await repo.save_document(document)

    # Atualiza o status do documento
    updated = await repo.update_document_status(document.id, DocumentStatus.PROCESSING)

    # Verifica se a atualização foi bem-sucedida
    assert updated is True

    # Recupera o documento atualizado
    updated_document = await repo.get_document(document.id)

    # Verifica se o status foi atualizado
    assert updated_document.status == DocumentStatus.PROCESSING


@pytest.mark.asyncio
async def test_save_transactions(postgres_repo, sample_document_dict):
    """Testa salvar transações no banco de dados."""
    # Cria o repositório
    repo = postgres_repo

    # Cria e salva um documento
    document = Document(**sample_document_dict)
    await repo.save_document(document)

    # Cria transações de teste
    transactions = [
        Transaction(
            id=uuid.uuid4(),
            document_id=document.id,
            user_id=document.user_id,
            date=datetime.now().date(),
            description="TRANSFERÊNCIA RECEBIDA - TESTE",
            amount=Decimal("1000.00"),
            type=TransactionType.CREDIT,
            method="TED",
            categories=["salário"],
            confidence_score=0.95
        ),
        Transaction(
            id=uuid.uuid4(),
            document_id=document.id,
            user_id=document.user_id,
            date=datetime.now().date(),
            description="PAGAMENTO - CONTA DE LUZ",
            amount=Decimal("150.25"),
            type=TransactionType.DEBIT,
            method="BOLETO",
            categories=["utilidades", "conta de luz"],
            confidence_score=0.92
        )
    ]

    # Salva as transações
    saved_transactions = await repo.save_transactions(transactions)

    # Verifica se as transações foram salvas corretamente
    assert len(saved_transactions) == 2

    # Recupera as transações do documento
    retrieved_transactions = await repo.get_transactions_by_document(document.id)

    # Verifica se as transações recuperadas correspondem às originais
    assert len(retrieved_transactions) == 2

    # Verifica se os IDs correspondem
    saved_ids = {tx.id for tx in saved_transactions}
    retrieved_ids = {tx.id for tx in retrieved_transactions}
    assert saved_ids == retrieved_ids


@pytest.mark.asyncio
async def test_get_transactions_by_user(postgres_repo, sample_document_dict):
    """Testa recuperar transações por ID de usuário."""
    # Cria o repositório
    repo = postgres_repo

    # Cria e salva um documento
    document = Document(**sample_document_dict)
    await repo.save_document(document)

    # Cria e salva transações
    transactions = [
        Transaction(
            id=uuid.uuid4(),
            document_id=document.id,
            user_id=document.user_id,
            date=datetime.now().date(),
            description="TRANSFERÊNCIA RECEBIDA - TESTE",
            amount=Decimal("1000.00"),
            type=TransactionType.CREDIT,
            method="TED",
            categories=["salário"],
            confidence_score=0.95
        ),
        Transaction(
            id=uuid.uuid4(),
            document_id=document.id,
            user_id=document.user_id,
            date=datetime.now().date(),
            description="PAGAMENTO - CONTA DE LUZ",
            amount=Decimal("150.25"),
            type=TransactionType.DEBIT,
            method="BOLETO",
            categories=["utilidades", "conta de luz"],
            confidence_score=0.92
        )
    ]

    await repo.save_transactions(transactions)

    # Recupera transações por usuário
    user_transactions = await repo.get_transactions_by_user(document.user_id, limit=10, offset=0)

    # Verifica se as transações foram recuperadas corretamente
    assert len(user_transactions) == 2

    # Verifica se pertencem ao usuário correto
    for tx in user_transactions:
        assert tx.user_id == document.user_id


@pytest.mark.asyncio
async def test_nonexistent_document(postgres_repo):
    """Testa comportamento ao buscar documento inexistente."""
    # Cria o repositório
    repo = postgres_repo

    # Tenta recuperar um documento inexistente
    nonexistent_doc = await repo.get_document(999999)

    # Verifica que retorna None
    assert nonexistent_doc is None


@pytest.mark.asyncio
async def test_update_nonexistent_document(postgres_repo):
    """Testa atualizar status de documento inexistente."""
    # Cria o repositório
    repo = postgres_repo

    # Tenta atualizar um documento inexistente
    updated = await repo.update_document_status(999999, DocumentStatus.PROCESSING)

    # Verifica que a atualização falha
    assert updated is False