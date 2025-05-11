import logging
import re
from typing import List, Optional

from financial_document_processor.adapters.ai.ai_provider import AIProvider
from financial_document_processor.domain.transaction import Transaction
from financial_document_processor.services.parsers.parser import DocumentParser

logger = logging.getLogger(__name__)


class BankStatementParser(DocumentParser):
    """
    Parser para extratos bancários.

    Implementa a lógica de extração específica para extratos bancários,
    combinando regras baseadas em padrões e processamento com IA.
    """

    def __init__(self, ai_provider: AIProvider):
        """
        Inicializa o parser de extratos bancários.

        Args:
            ai_provider: Provedor de IA para assistir na extração
        """
        self.ai_provider = ai_provider

        # Expressões regulares comuns para extratos bancários
        # Nota: Padrões simplificados - em uma implementação real seriam mais robustos
        self.date_patterns = [
            re.compile(r'(\d{2}/\d{2}/\d{4})'),  # DD/MM/YYYY
            re.compile(r'(\d{2}/\d{2}/\d{2})'),  # DD/MM/YY
            re.compile(r'(\d{2}\.\d{2}\.\d{4})'),  # DD.MM.YYYY
            re.compile(r'(\d{2}-\d{2}-\d{4})'),  # DD-MM-YYYY
        ]

        # Padrões para transações (variam muito por banco)
        self.transaction_patterns = {
            # Exemplo simplificado - em uma implementação real seria mais extenso
            'pix': re.compile(r'pix', re.IGNORECASE),
            'ted': re.compile(r'ted|transferencia', re.IGNORECASE),
            'boleto': re.compile(r'boleto|fatura', re.IGNORECASE),
            'saque': re.compile(r'saque|retirada', re.IGNORECASE),
            'deposito': re.compile(r'deposito', re.IGNORECASE),
        }

        self.amount_pattern = re.compile(r'[\d.,]+')

    async def parse(
            self,
            text_content: str,
            predefined_categories: Optional[List[str]] = None
    ) -> List[Transaction]:
        """
        Parseia um extrato bancário para extrair transações.

        Esta implementação delega a extração para o provedor de IA,
        pois os extratos podem variar significativamente entre bancos.

        Args:
            text_content: Texto extraído do extrato bancário
            predefined_categories: Lista de categorias predefinidas (opcional)

        Returns:
            Lista de transações extraídas
        """
        # Neste caso, delega o parsing para o provedor de IA
        # devido à grande variação nos formatos de extratos
        return await self.ai_provider.extract_transactions(
            text_content=text_content,
            document_type="bank_statement",
            predefined_categories=predefined_categories
        )
