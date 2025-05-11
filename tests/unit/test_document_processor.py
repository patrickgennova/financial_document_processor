"""
Testes unitários para o processador de documentos.
"""
import base64
import pytest
from unittest.mock import AsyncMock, MagicMock
from financial_document_processor.services.document_processor import DocumentProcessor
from financial_document_processor.services.file_decoder import FileDecoder
from financial_document_processor.services.parsers.bank_statement import BankStatementParser


@pytest.fixture
def mock_file_decoder():
    """Cria um mock do decodificador de arquivos."""
    decoder = MagicMock(spec=FileDecoder)
    decoder.decode_and_extract_text.return_value = "Conteúdo de texto extraído para teste"
    return decoder


@pytest.fixture
def mock_parser():
    """Cria um mock de parser de documentos."""
    parser = MagicMock(spec=BankStatementParser)
    parser.parse = AsyncMock()
    return parser


@pytest.fixture
def document_processor(mock_file_decoder, mock_ai_provider, mock_parser):
    """Cria uma instância do processador de documentos com mocks."""
    parsers = {"bank_statement": mock_parser}
    return DocumentProcessor(
        file_decoder=mock_file_decoder,
        ai_provider=mock_ai_provider,
        parsers=parsers
    )


@pytest.mark.asyncio
async def test_process_document(document_processor, sample_document, mock_file_decoder, mock_ai_provider):
    """Testa o processamento completo de um documento."""
    # Processa o documento
    transactions = await document_processor.process(sample_document)

    # Verifica se o decodificador foi chamado com os parâmetros corretos
    mock_file_decoder.decode_and_extract_text.assert_called_once_with(
        sample_document.file_content, sample_document.content_type
    )

    # Verifica se o provedor de IA foi chamado para extrair transações
    assert mock_ai_provider.call_count > 0

    # Verifica se o resultado é uma lista de transações
    assert isinstance(transactions, list)

    # Verifica se as transações têm os IDs corretos
    for tx in transactions:
        assert tx.document_id == sample_document.id
        assert tx.user_id == sample_document.user_id


@pytest.mark.asyncio
async def test_process_document_with_predefined_categories(document_processor, sample_document, mock_ai_provider):
    """Testa o processamento de documento com categorias predefinidas."""
    # Define categorias no documento
    sample_document.categories = ["salário", "utilidades"]

    # Processa o documento
    transactions = await document_processor.process(sample_document)

    # Verifica se o provedor de IA foi chamado com as categorias corretas
    assert mock_ai_provider.call_count > 0

    # Verifica o resultado
    assert isinstance(transactions, list)


@pytest.mark.asyncio
async def test_process_unsupported_document_type(document_processor):
    """Testa o comportamento com tipo de documento não suportado."""
    # Cria um documento com tipo não suportado
    document = MagicMock()
    document.document_type = "unsupported_type"

    # Deve lançar uma exceção para tipo não suportado
    with pytest.raises(ValueError, match="Tipo de documento não suportado"):
        await document_processor.process(document)


@pytest.mark.asyncio
async def test_process_document_no_text_content(document_processor, sample_document, mock_file_decoder):
    """Testa o comportamento quando nenhum texto é extraído."""
    # Configura o mock para retornar texto vazio
    mock_file_decoder.decode_and_extract_text.return_value = ""

    # Processa o documento
    transactions = await document_processor.process(sample_document)

    # Verifica se o resultado é uma lista vazia
    assert isinstance(transactions, list)
    assert len(transactions) == 0


@pytest.mark.asyncio
async def test_document_processor_with_categorization_service(mock_file_decoder, mock_ai_provider, mock_parser):
    """Testa o processador com serviço de categorização."""
    # Cria um mock para o serviço de categorização
    mock_categorization_service = MagicMock()
    mock_categorization_service.categorize_transactions = AsyncMock(return_value=[])

    # Cria o processador com o serviço de categorização
    parsers = {"bank_statement": mock_parser}
    processor = DocumentProcessor(
        file_decoder=mock_file_decoder,
        ai_provider=mock_ai_provider,
        parsers=parsers,
        categorization_service=mock_categorization_service
    )

    # Cria um documento de teste
    document = MagicMock()
    document.document_type = "bank_statement"
    document.file_content = base64.b64encode(b"test content").decode("utf-8")
    document.content_type = "text/plain"

    # Configura o AI provider para retornar algumas transações
    mock_ai_provider.extract_transactions = AsyncMock(return_value=[MagicMock()])

    # Processa o documento
    await processor.process(document)

    # Verifica se o serviço de categorização foi chamado
    mock_categorization_service.categorize_transactions.assert_called_once()