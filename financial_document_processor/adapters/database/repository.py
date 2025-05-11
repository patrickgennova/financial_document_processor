from abc import ABC, abstractmethod
from typing import List, Optional

from financial_document_processor.domain.document import Document, DocumentStatus
from financial_document_processor.domain.transaction import Transaction


class Repository(ABC):
    """
    Interface base para repositórios de dados.

    Define o contrato que todos os repositórios de dados devem implementar.
    """

    @abstractmethod
    async def connect(self):
        """Estabelece a conexão com o banco de dados."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Encerra a conexão com o banco de dados."""
        pass

    @abstractmethod
    async def save_document(self, document: Document) -> Document:
        """
        Salva um documento no banco de dados.

        Args:
            document: Documento a ser salvo

        Returns:
            Documento salvo com possíveis campos atualizados (como ID)
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: int) -> Optional[Document]:
        """
        Obtém um documento pelo ID.

        Args:
            document_id: ID do documento

        Returns:
            Documento encontrado ou None
        """
        pass

    @abstractmethod
    async def update_document_status(
            self, document_id: int, status: DocumentStatus
    ) -> bool:
        """
        Atualiza o status de um documento.

        Args:
            document_id: ID do documento
            status: Novo status

        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    async def save_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Salva uma lista de transações no banco de dados.

        Args:
            transactions: Lista de transações a ser salva

        Returns:
            Lista de transações salvas com possíveis campos atualizados
        """
        pass

    @abstractmethod
    async def get_transactions_by_document(
            self, document_id: int
    ) -> List[Transaction]:
        """
        Obtém todas as transações associadas a um documento.

        Args:
            document_id: ID do documento

        Returns:
            Lista de transações
        """
        pass

    @abstractmethod
    async def get_transactions_by_user(
            self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[Transaction]:
        """
        Obtém transações de um usuário.

        Args:
            user_id: ID do usuário
            limit: Número máximo de transações a retornar
            offset: Offset para paginação

        Returns:
            Lista de transações
        """
        pass
