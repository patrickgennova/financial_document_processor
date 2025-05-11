from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel

from financial_document_processor.domain.transaction import Transaction


class AIRequest(BaseModel):
    """
    Modelo base para requisições a provedores de IA.
    """
    prompt: str
    max_tokens: Optional[int] = None
    temperature: float = 0.0  # Baixar temperatura para resultados mais precisos
    system_message: Optional[str] = None
    stop_sequences: Optional[List[str]] = None
    model: Optional[str] = None


class AIResponse(BaseModel):
    """
    Modelo base para respostas de provedores de IA.
    """
    content: str
    model: str
    tokens_used: int
    cost: float  # Custo estimado da chamada em USD


class AIProvider(ABC):
    """
    Interface abstrata para provedores de IA.

    Esta classe define o contrato que todos os provedores de IA devem implementar.
    """

    @abstractmethod
    async def extract_transactions(
            self,
            text_content: str,
            document_type: str,
            predefined_categories: Optional[List[str]] = None,
            document_id: int = 0,
            user_id: int = 0,
    ) -> List[Transaction]:
        """
        Extrai transações de um conteúdo textual utilizando IA.

        Args:
            text_content: Texto extraído do documento
            document_type: Tipo do documento (ex: bank_statement)
            predefined_categories: Lista de categorias predefinidas, se disponível
            document_id: ID do documento
            user_id: ID do usuario

        Returns:
            Lista de transações extraídas
        """
        pass

    @abstractmethod
    async def categorize_transactions(
            self,
            transactions: List[Transaction],
            predefined_categories: Optional[List[str]] = None
    ) -> List[Transaction]:
        """
        Categoriza uma lista de transações utilizando IA.

        Args:
            transactions: Lista de transações a serem categorizadas
            predefined_categories: Lista de categorias predefinidas, se disponível

        Returns:
            Mesma lista de transações com categorias atualizadas
        """
        pass

    @abstractmethod
    async def generate_completion(self, request: AIRequest) -> AIResponse:
        """
        Método de baixo nível para gerar completions diretamente.

        Args:
            request: Parâmetros da requisição

        Returns:
            Resposta do modelo de IA
        """
        pass

    @abstractmethod
    def get_cost_per_1k_tokens(self) -> float:
        """
        Retorna o custo por 1000 tokens para o provedor atual.

        Returns:
            Custo em USD por 1000 tokens
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nome do provedor de IA.

        Returns:
            String com o nome do provedor
        """
        pass
