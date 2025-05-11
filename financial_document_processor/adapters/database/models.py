"""
Modelos SQLAlchemy para o banco de dados.

Este módulo define os modelos ORM usando SQLAlchemy, que são usados para
gerar as migrações de banco de dados e para interagir com o banco de dados.
"""
import uuid
from datetime import datetime, UTC
from enum import Enum

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum as SQLAEnum,
    ForeignKey, Index, MetaData, Numeric,
    String, Text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class DocumentStatusEnum(str, Enum):
    """Status de um documento no fluxo de processamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class TransactionTypeEnum(str, Enum):
    """Tipos de transações bancárias."""
    CREDIT = "credit"  # Entrada de dinheiro
    DEBIT = "debit"  # Saída de dinheiro


class TransactionMethodEnum(str, Enum):
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


class Document(Base):
    """Modelo SQLAlchemy para documentos financeiros."""
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True)
    external_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_content = Column(Text, nullable=False)
    categories = Column(JSONB, nullable=True)
    status = Column(SQLAEnum(DocumentStatusEnum), nullable=False, default=DocumentStatusEnum.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC) )
    updated_at = Column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    transactions = relationship("Transaction", back_populates="document", cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index("idx_documents_user_id", user_id),
        Index("idx_documents_external_id", external_id),
        Index("idx_documents_status", status),
    )


class Transaction(Base):
    """Modelo SQLAlchemy para transações financeiras."""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(SQLAEnum(TransactionTypeEnum), nullable=False)
    method = Column(SQLAEnum(TransactionMethodEnum), nullable=True)
    categories = Column(JSONB, nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))

    # Relacionamentos
    document = relationship("Document", back_populates="transactions")

    # Índices
    __table_args__ = (
        Index("idx_transactions_document_id", document_id),
        Index("idx_transactions_user_id", user_id),
        Index("idx_transactions_date", date),
        Index("idx_transactions_type", type),
    )