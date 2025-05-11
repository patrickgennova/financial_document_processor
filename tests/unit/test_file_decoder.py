"""
Testes unitários para o decodificador de arquivos.
"""
import base64
import pytest

from financial_document_processor.services.file_decoder import FileDecoder


@pytest.fixture
def file_decoder():
    """Cria uma instância do FileDecoder para os testes."""
    return FileDecoder()


@pytest.fixture
def sample_text_content():
    """Conteúdo de texto de amostra para testes."""
    return "Este é um arquivo de texto de exemplo para o teste."


@pytest.fixture
def sample_text_base64(sample_text_content):
    """Conteúdo de texto codificado em base64."""
    return base64.b64encode(sample_text_content.encode("utf-8")).decode("utf-8")


def test_decode_text_file(file_decoder, sample_text_content, sample_text_base64):
    """Testa a decodificação de um arquivo de texto."""
    # Decodifica o conteúdo
    decoded_text = file_decoder.decode_and_extract_text(
        sample_text_base64, "text/plain"
    )

    # Verifica se o texto decodificado corresponde ao original
    assert decoded_text == sample_text_content


def test_decode_csv_file(file_decoder):
    """Testa a decodificação de um arquivo CSV."""
    # Cria um conteúdo CSV de amostra
    csv_content = "Data,Descrição,Valor\n2023-01-01,Teste,100.00"
    csv_base64 = base64.b64encode(csv_content.encode("utf-8")).decode("utf-8")

    # Decodifica o conteúdo
    decoded_text = file_decoder.decode_and_extract_text(
        csv_base64, "text/csv"
    )

    # Verifica se o texto decodificado corresponde ao original
    assert decoded_text == csv_content


def test_unsupported_content_type(file_decoder, sample_text_base64):
    """Testa o comportamento com um tipo de conteúdo não suportado."""
    # Deve lançar uma exceção para tipo de conteúdo não suportado
    with pytest.raises(ValueError, match="Tipo de conteúdo não suportado"):
        file_decoder.decode_and_extract_text(
            sample_text_base64, "application/unsupported"
        )


@pytest.mark.parametrize(
    "content_type,expected_substring",
    [
        ("text/plain", "Este é um arquivo"),
        ("text/csv", "Data,Descrição"),
    ],
)
def test_multiple_content_types(file_decoder, content_type, expected_substring):
    """Testa vários tipos de conteúdo."""
    # Cria conteúdo específico para cada tipo
    if content_type == "text/plain":
        content = "Este é um arquivo de texto para teste."
    elif content_type == "text/csv":
        content = "Data,Descrição,Valor\n2023-01-01,Teste,100.00"
    else:
        content = "Conteúdo genérico"

    # Codifica o conteúdo
    content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # Decodifica o conteúdo
    decoded_text = file_decoder.decode_and_extract_text(
        content_base64, content_type
    )

    # Verifica se o texto decodificado contém a substring esperada
    assert expected_substring in decoded_text

# Testes específicos para PDF e imagens podem ser adicionados
# conforme necessário, usando mocks para evitar dependências externas