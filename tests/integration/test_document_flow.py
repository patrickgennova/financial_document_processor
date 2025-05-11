"""
Testes de integração para o fluxo completo de processamento de documentos.
"""
import base64
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from financial_document_processor.domain.document import Document, DocumentStatus
from financial_document_processor.services.categorization import CategorizationService
from financial_document_processor.services.document_processor import DocumentProcessor
from financial_document_processor.services.file_decoder import FileDecoder
from financial_document_processor.services.parsers.bank_statement import BankStatementParser


@pytest.fixture
def test_file_content():
    """Fornece um conteúdo de arquivo de teste."""
    # Cria um texto de exemplo para o teste
    sample_text = """
    EXTRATO BANCÁRIO
    Cliente: João Silva
    Conta: 12345-6
    Período: 01/05/2023 a 31/05/2023

    DATA       DESCRIÇÃO                      VALOR      TIPO
    03/05/2023 TRANSFERÊNCIA RECEBIDA - SALÁRIO 3500,00   C
    05/05/2023 PAGAMENTO - CONTA DE LUZ         150,25   D
    10/05/2023 PAGAMENTO - SUPERMERCADO         350,75   D
    15/05/2023 TRANSFERÊNCIA PIX RECEBIDA       200,00   C
    20/05/2023 PAGAMENTO - INTERNET             120,00   D
    25/05/2023 SAQUE EM CAIXA ELETRÔNICO        500,00   D

    SALDO ANTERIOR: 1.200,00
    SALDO ATUAL: 3.779,00
    """

    # Codifica para base64
    return base64.b64encode(sample_text.encode("utf-8")).decode("utf-8")


@pytest.fixture
def setup_processors(mock_ai_provider, async_session, postgres_repo):
    """Configura os processadores para teste."""
    # Cria os componentes
    file_decoder = FileDecoder()
    parser = BankStatementParser(ai_provider=mock_ai_provider)

    # Cria o repositório
    repo = postgres_repo
    repo.pool = async_session

    # Cria o serviço de categorização
    categorization_service = CategorizationService(
        ai_provider=mock_ai_provider,
        batch_size=5
    )

    # Cria o processador de documentos
    document_processor = DocumentProcessor(
        file_decoder=file_decoder,
        ai_provider=mock_ai_provider,
        parsers={"bank_statement": parser},
        categorization_service=categorization_service
    )

    return document_processor, repo


@pytest.mark.asyncio
async def test_full_document_processing(setup_processors, test_file_content):
    """Testa o fluxo completo de processamento de documento."""
    document_processor, repo = setup_processors

    # Cria um documento de teste
    document = Document(
        id=12345,
        external_id=uuid4(),
        user_id=98765,
        document_type="bank_statement",
        filename="extrato_teste.txt",
        content_type="text/plain",
        file_content=test_file_content,
        categories=["salário", "utilidades"],
        status=DocumentStatus.PENDING,
        created_at=MagicMock(),
        updated_at=MagicMock()
    )

    # Salva o documento no banco
    await repo.save_document(document)

    # Processa o documento
    transactions = await document_processor.process(document)

    # Verifica se transações foram extraídas
    assert len(transactions) > 0

    # Salva as transações
    await repo.save_transactions(transactions)

    # Atualiza o status do documento
    await repo.update_document_status(document.id, DocumentStatus.PROCESSED)

    # Verifica se o documento foi processado corretamente
    processed_document = await repo.get_document(document.id)
    assert processed_document.status == DocumentStatus.PROCESSED

    # Verifica se as transações foram salvas corretamente
    saved_transactions = await repo.get_transactions_by_document(document.id)
    assert len(saved_transactions) == len(transactions)

    # Verifica se as transações têm categorias
    assert all(len(tx.categories) > 0 for tx in saved_transactions)


@pytest.mark.asyncio
async def test_document_processing_error_handling(setup_processors, test_file_content):
    """Testa o tratamento de erros no processamento de documentos."""
    document_processor, repo = setup_processors

    # Cria um documento com tipo não suportado
    document = Document(
        id=54321,
        external_id=uuid4(),
        user_id=98765,
        document_type="unsupported_type",  # Tipo não suportado
        filename="documento_teste.txt",
        content_type="text/plain",
        file_content=test_file_content,
        status=DocumentStatus.PENDING,
        created_at=MagicMock(),
        updated_at=MagicMock()
    )

    # Salva o documento no banco
    await repo.save_document(document)

    # Tenta processar o documento (deve lançar exceção)
    with pytest.raises(ValueError, match="Tipo de documento não suportado"):
        await document_processor.process(document)

    # Simula o tratamento de erro que seria feito pelo handler principal
    await repo.update_document_status(document.id, DocumentStatus.FAILED)

    # Verifica se o status foi atualizado corretamente
    failed_document = await repo.get_document(document.id)
    assert failed_document.status == DocumentStatus.FAILED


@pytest.mark.asyncio
async def test_empty_document_handling(setup_processors):
    """Testa o tratamento de documentos vazios."""
    document_processor, repo = setup_processors

    # Cria um documento com conteúdo vazio
    document = Document(
        id=67890,
        external_id=uuid4(),
        user_id=98765,
        document_type="bank_statement",
        filename="documento_vazio.txt",
        content_type="text/plain",
        file_content=base64.b64encode(b"").decode("utf-8"),  # Conteúdo vazio
        status=DocumentStatus.PENDING,
        created_at=MagicMock(),
        updated_at=MagicMock()
    )

    # Salva o documento no banco
    await repo.save_document(document)

    # Processa o documento (não deve lançar exceção, mas retornar lista vazia)
    transactions = await document_processor.process(document)

    # Verifica se não foram extraídas transações
    assert isinstance(transactions, list)
    assert len(transactions) == 0

    # Atualiza o status do documento como processado, mesmo sem transações
    await repo.update_document_status(document.id, DocumentStatus.PROCESSED)

    # Verifica se o status foi atualizado corretamente
    processed_document = await repo.get_document(document.id)
    assert processed_document.status == DocumentStatus.PROCESSED


@pytest.mark.asyncio
async def test_predefined_categories_processing(setup_processors, test_file_content):
    """Testa o processamento de documento com categorias predefinidas."""
    document_processor, repo = setup_processors

    # Cria um documento com categorias predefinidas
    document = Document(
        id=11111,
        external_id=uuid4(),
        user_id=98765,
        document_type="bank_statement",
        filename="extrato_com_categorias.txt",
        content_type="text/plain",
        file_content=test_file_content,
        categories=["salário", "água", "luz", "internet", "mercado"],  # Categorias predefinidas
        status=DocumentStatus.PENDING,
        created_at=MagicMock(),
        updated_at=MagicMock()
    )

    # Salva o documento no banco
    await repo.save_document(document)

    # Processa o documento
    transactions = await document_processor.process(document)

    # Verifica se transações foram extraídas
    assert len(transactions) > 0

    # Verifica se as categorias das transações são compatíveis com as predefinidas
    for tx in transactions:
        # Ou a transação tem categorias válidas ou não tem categorias
        if tx.categories:
            # Pelo menos uma categoria deve estar na lista predefinida
            assert any(cat in document.categories for cat in tx.categories)

    # Salva as transações
    await repo.save_transactions(transactions)

    # Verifica se as transações foram salvas corretamente
    saved_transactions = await repo.get_transactions_by_document(document.id)
    assert len(saved_transactions) == len(transactions)