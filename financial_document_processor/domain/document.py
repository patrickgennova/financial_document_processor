from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Status do documento no fluxo de processamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(BaseModel):
    """
    Modelo que representa um documento financeiro a ser processado.

    Este modelo corresponde diretamente à estrutura JSON recebida do Kafka.
    """
    id: int = Field(description="ID interno do documento")
    external_id: UUID = Field(description="ID externo do documento")
    user_id: int = Field(description="ID do usuário dono do documento")
    document_type: str = Field(description="Tipo do documento (ex: bank_statement)")
    filename: str = Field(description="Nome do arquivo original")
    content_type: str = Field(description="Tipo MIME do conteúdo (ex: application/pdf)")
    file_content: str = Field(description="Conteúdo do arquivo em Base64")
    categories: Optional[List[str]] = Field(
        default=None, description="Categorias pré-definidas para o documento"
    )
    status: DocumentStatus = Field(description="Status atual do documento")
    created_at: datetime = Field(description="Data de criação do registro")
    updated_at: datetime = Field(description="Data da última atualização")

    class Config:
        """Configurações do modelo Pydantic."""
        frozen = True

