from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, field_validator, model_validator


class TransactionType(str, Enum):
    """Tipos de transações bancárias."""
    CREDIT = "credit"  # Entrada de dinheiro
    DEBIT = "debit"  # Saída de dinheiro


class TransactionMethod(str, Enum):
    """Métodos de transação."""
    PIX = "pix"
    TED = "ted"
    DOC = "doc"
    BOLETO = "boleto"
    PAYMENT = "payment"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    LOAN = "loan"
    OTHER = "other"


class Transaction(BaseModel):
    """
    Modelo que representa uma transação financeira extraída de um documento.
    """
    id: UUID
    document_id: int
    user_id: int
    date: date
    description: str
    amount: Decimal
    type: TransactionType
    method: Optional[TransactionMethod] = None
    categories: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    created_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def set_defaults(cls, data: Any) -> Any:
        """Define valores padrão para campos que não foram fornecidos."""
        if isinstance(data, dict):
            # Define ID com uuid4 se não fornecido
            if 'id' not in data:
                data['id'] = uuid4()

            # Define categorias como lista vazia se não fornecido
            if 'categories' not in data or data['categories'] is None:
                data['categories'] = []

            # Define data de criação se não fornecida
            if 'created_at' not in data or data['created_at'] is None:
                data['created_at'] = datetime.now()

        return data

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, amount: Decimal) -> Decimal:
        """Valida que o valor da transação não é zero."""
        if amount == Decimal("0"):
            raise ValueError("O valor da transação não pode ser zero")
        return amount

    class Config:
        """Configuração para serialização."""
        json_encoders = {
            Decimal: lambda v: str(v),
            UUID: lambda v: str(v),
        }
