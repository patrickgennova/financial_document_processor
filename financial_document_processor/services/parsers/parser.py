from abc import ABC, abstractmethod
from typing import List, Optional

from financial_document_processor.domain.transaction import Transaction


class DocumentParser(ABC):
    """
    Interface base para parsers de documentos financeiros.

    Os parsers são responsáveis por extrair transações de tipos específicos
    de documentos financeiros.
    """

    @abstractmethod
    async def parse(
            self,
            text_content: str,
            predefined_categories: Optional[List[str]] = None
    ) -> List[Transaction]:
        """
        Parseia o conteúdo de texto extraído do documento e retorna as transações.

        Args:
            text_content: Texto extraído do documento
            predefined_categories: Lista de categorias predefinidas (opcional)

        Returns:
            Lista de transações extraídas
        """
        pass