"""
Testes unitários para o serviço de engenharia de prompts.
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from financial_document_processor.domain.transaction import Transaction, TransactionType, TransactionMethod
from financial_document_processor.services.prompt_engineering import PromptEngineering


@pytest.fixture
def prompt_engineering():
    """Cria uma instância do serviço de engenharia de prompts para os testes."""
    return PromptEngineering()


@pytest.fixture
def sample_text_content():
    """Fornece um conteúdo de texto de exemplo para testes."""
    return """
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


@pytest.fixture
def sample_transactions():
    """Cria uma lista de transações de exemplo para testes."""
    return [
        Transaction(
            id=uuid4(),
            document_id=1,
            user_id=123,
            date=date.today(),
            description="TRANSFERÊNCIA RECEBIDA - SALÁRIO",
            amount=Decimal("3500.00"),
            type=TransactionType.CREDIT,
            method=TransactionMethod.TED,
            categories=[]
        ),
        Transaction(
            id=uuid4(),
            document_id=1,
            user_id=123,
            date=date.today(),
            description="PAGAMENTO - CONTA DE LUZ",
            amount=Decimal("150.25"),
            type=TransactionType.DEBIT,
            method=TransactionMethod.BOLETO,
            categories=[]
        ),
        Transaction(
            id=uuid4(),
            document_id=1,
            user_id=123,
            date=date.today(),
            description="PAGAMENTO - SUPERMERCADO",
            amount=Decimal("350.75"),
            type=TransactionType.DEBIT,
            method=TransactionMethod.PAYMENT,
            categories=[]
        )
    ]


def test_create_extraction_prompt_openai(prompt_engineering, sample_text_content):
    """Testa a criação de prompt de extração para OpenAI."""
    prompt = prompt_engineering.create_extraction_prompt(
        text_content=sample_text_content,
        document_type="bank_statement",
        provider="openai"
    )

    # Verifica se o prompt contém elementos esperados
    assert "# Tarefa: Extração de Transações Financeiras" in prompt
    assert "bank_statement" in prompt
    assert sample_text_content in prompt
    assert "```json" in prompt
    assert "transactions" in prompt


def test_create_extraction_prompt_gemini(prompt_engineering, sample_text_content):
    """Testa a criação de prompt de extração para Gemini."""
    prompt = prompt_engineering.create_extraction_prompt(
        text_content=sample_text_content,
        document_type="bank_statement",
        provider="gemini"
    )

    # Verifica se o prompt contém elementos esperados
    assert "Extraia todas as transações financeiras" in prompt
    assert "bank_statement" in prompt
    assert sample_text_content in prompt
    assert "```json" in prompt
    assert "DIRETRIZES DE PRECISÃO" in prompt


def test_create_extraction_prompt_claude(prompt_engineering, sample_text_content):
    """Testa a criação de prompt de extração para Claude."""
    prompt = prompt_engineering.create_extraction_prompt(
        text_content=sample_text_content,
        document_type="bank_statement",
        provider="claude"
    )

    # Verifica se o prompt contém elementos esperados
    assert "<documento>" in prompt
    assert sample_text_content in prompt
    assert "</documento>" in prompt
    assert "bank_statement" in prompt
    assert "```json" in prompt
    assert "Siga estas regras rigorosamente" in prompt


def test_create_extraction_prompt_with_categories(prompt_engineering, sample_text_content):
    """Testa a criação de prompt de extração com categorias predefinidas."""
    predefined_categories = ["salário", "luz", "água", "supermercado"]

    prompt = prompt_engineering.create_extraction_prompt(
        text_content=sample_text_content,
        document_type="bank_statement",
        predefined_categories=predefined_categories,
        provider="gemini"
    )

    # Verifica se as categorias estão incluídas no prompt
    assert "salário" in prompt
    assert "luz" in prompt
    assert "água" in prompt
    assert "supermercado" in prompt


def test_create_categorization_prompt_openai(prompt_engineering, sample_transactions):
    """Testa a criação de prompt de categorização para OpenAI."""
    prompt = prompt_engineering.create_categorization_prompt(
        transactions=sample_transactions,
        provider="openai"
    )

    # Verifica se o prompt contém elementos esperados
    assert "# Tarefa: Categorização de Transações Financeiras" in prompt
    assert "TRANSFERÊNCIA RECEBIDA - SALÁRIO" in prompt
    assert "PAGAMENTO - CONTA DE LUZ" in prompt
    assert "PAGAMENTO - SUPERMERCADO" in prompt
    assert "categories" in prompt
    assert "confidence_score" in prompt


def test_create_categorization_prompt_gemini(prompt_engineering, sample_transactions):
    """Testa a criação de prompt de categorização para Gemini."""
    prompt = prompt_engineering.create_categorization_prompt(
        transactions=sample_transactions,
        provider="gemini"
    )

    # Verifica se o prompt contém elementos esperados
    assert "Categorize as seguintes transações financeiras" in prompt
    assert "TRANSFERÊNCIA RECEBIDA - SALÁRIO" in prompt
    assert "PAGAMENTO - CONTA DE LUZ" in prompt
    assert "PAGAMENTO - SUPERMERCADO" in prompt
    assert "DIRETRIZES DE CATEGORIZAÇÃO" in prompt
    assert "categories" in prompt
    assert "confidence_score" in prompt


def test_create_categorization_prompt_claude(prompt_engineering, sample_transactions):
    """Testa a criação de prompt de categorização para Claude."""
    prompt = prompt_engineering.create_categorization_prompt(
        transactions=sample_transactions,
        provider="claude"
    )

    # Verifica se o prompt contém elementos esperados
    assert "<transações>" in prompt
    assert "</transações>" in prompt
    assert "TRANSFERÊNCIA RECEBIDA - SALÁRIO" in prompt
    assert "PAGAMENTO - CONTA DE LUZ" in prompt
    assert "PAGAMENTO - SUPERMERCADO" in prompt
    assert "Categorize cada transação financeira acima" in prompt
    assert "categories" in prompt
    assert "confidence_score" in prompt


def test_create_categorization_prompt_with_predefined_categories(prompt_engineering, sample_transactions):
    """Testa a criação de prompt de categorização com categorias predefinidas."""
    predefined_categories = ["salário", "luz", "água", "supermercado"]

    prompt = prompt_engineering.create_categorization_prompt(
        transactions=sample_transactions,
        predefined_categories=predefined_categories,
        provider="gemini"
    )

    # Verifica se as categorias estão incluídas no prompt
    assert "salário" in prompt
    assert "luz" in prompt
    assert "água" in prompt
    assert "supermercado" in prompt
    assert "Você deve usar APENAS as seguintes categorias" in prompt


def test_text_content_length_limit(prompt_engineering):
    """Testa o limite de comprimento do texto para evitar exceder limites de tokens."""
    # Cria um texto muito longo
    long_text = "Lorem ipsum dolor sit amet. " * 1000  # Texto com mais de 15.000 caracteres

    prompt = prompt_engineering.create_extraction_prompt(
        text_content=long_text,
        document_type="bank_statement",
        provider="gemini"
    )

    # Verifica se o texto foi truncado
    assert "..." in prompt
    assert len(prompt) < len(long_text) + 1000  # Verifica se foi significativamente reduzido


def test_provider_fallback(prompt_engineering, sample_text_content):
    """Testa o fallback para OpenAI quando um provedor desconhecido é especificado."""
    prompt = prompt_engineering.create_extraction_prompt(
        text_content=sample_text_content,
        document_type="bank_statement",
        provider="unknown_provider"  # Provedor inexistente
    )

    # Deve usar o template do OpenAI como fallback
    assert "# Tarefa: Extração de Transações Financeiras" in prompt


def test_create_categorization_prompt_empty_transactions(prompt_engineering):
    """Testa a criação de prompt de categorização com lista vazia de transações."""
    prompt = prompt_engineering.create_categorization_prompt(
        transactions=[],
        provider="gemini"
    )

    assert "transactions" in prompt