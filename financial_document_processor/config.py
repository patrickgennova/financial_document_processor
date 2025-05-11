import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class DatabaseSettings(BaseModel):
    """Configurações do banco de dados."""
    url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/financial_docs",
        description="URL de conexão com o banco de dados"
    )
    min_connections: int = Field(default=5, description="Número mínimo de conexões no pool")
    max_connections: int = Field(default=20, description="Número máximo de conexões no pool")


class KafkaSettings(BaseModel):
    """Configurações do Kafka."""
    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Lista de servidores Kafka"
    )
    consumer_group: str = Field(
        default="financial-document-processor",
        description="ID do grupo de consumidores"
    )
    documents_topic: str = Field(
        default="documents-to-process",
        description="Tópico para consumo de documentos"
    )
    processed_topic: str = Field(
        default="processed-documents",
        description="Tópico para envio de documentos processados"
    )


class AISettings(BaseModel):
    """Configurações para provedores de IA."""
    provider: str = Field(
        default="openai",
        description="Provedor de IA a ser utilizado (openai, gemini, claude)"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="Chave de API da OpenAI"
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="Modelo da OpenAI a ser utilizado"
    )
    openai_organization_id: Optional[str] = Field(
        default=None,
        description="ID da organização na OpenAI"
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Chave de API do Google Gemini"
    )
    gemini_model: str = Field(
        default="gemini-1.5-pro",
        description="Modelo do Gemini a ser utilizado"
    )
    claude_api_key: Optional[str] = Field(
        default=None,
        description="Chave de API da Anthropic Claude"
    )
    claude_model: str = Field(
        default="claude-3-opus-20240229",
        description="Modelo do Claude a ser utilizado"
    )
    batch_size: int = Field(
        default=10,
        description="Tamanho do lote para chamadas de API"
    )


class OCRSettings(BaseModel):
    """Configurações para OCR."""
    tesseract_path: Optional[str] = Field(
        default=None,
        description="Caminho para o executável do Tesseract OCR"
    )
    language: str = Field(
        default="por",
        description="Idioma para OCR (ex: por, eng, spa)"
    )


class AppSettings(BaseModel):
    """Configurações gerais da aplicação."""
    log_level: str = Field(
        default="INFO",
        description="Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    batch_size: int = Field(
        default=10,
        description="Tamanho máximo do lote para processamento"
    )
    max_retries: int = Field(
        default=3,
        description="Número máximo de tentativas para operações"
    )
    document_processing_timeout: int = Field(
        default=60,
        description="Timeout para processamento de documentos (segundos)"
    )


class Settings(BaseModel):
    """Configurações completas da aplicação."""
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    ai: AISettings = Field(default_factory=AISettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)


@lru_cache()
def get_settings() -> Settings:
    """
    Obtém as configurações da aplicação.

    Carrega as configurações a partir de variáveis de ambiente
    e aplica valores padrão quando não definidos.

    Returns:
        Objeto Settings com as configurações
    """
    app_settings = AppSettings(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        batch_size=int(os.getenv("BATCH_SIZE", "10")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        document_processing_timeout=int(os.getenv("DOCUMENT_PROCESSING_TIMEOUT", "60")),
    )

    db_settings = DatabaseSettings(
        url=os.getenv("DATABASE_URL", "postgresql://financial_docs:financial_docs@localhost:5432/financial_docs"),
        min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),
        max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
    )

    kafka_settings = KafkaSettings(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        consumer_group=os.getenv("KAFKA_CONSUMER_GROUP", "financial-document-processor"),
        documents_topic=os.getenv("KAFKA_DOCUMENTS_TOPIC", "documents-to-process"),
        processed_topic=os.getenv("KAFKA_PROCESSED_TOPIC", "processed-documents"),
    )

    ai_settings = AISettings(
        provider=os.getenv("AI_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        openai_organization_id=os.getenv("OPENAI_ORGANIZATION_ID"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        claude_api_key=os.getenv("ANTHROPIC_API_KEY"),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
        batch_size=int(os.getenv("AI_BATCH_SIZE", "10")),
    )

    ocr_settings = OCRSettings(
        tesseract_path=os.getenv("TESSERACT_PATH"),
        language=os.getenv("OCR_LANGUAGE", "por"),
    )

    return Settings(
        app=app_settings,
        database=db_settings,
        kafka=kafka_settings,
        ai=ai_settings,
        ocr=ocr_settings,
    )