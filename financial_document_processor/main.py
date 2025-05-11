import asyncio
import logging
import signal
import sys
from typing import Dict

from financial_document_processor.adapters.ai import create_ai_provider
from financial_document_processor.adapters.database.postgres import PostgresRepository
from financial_document_processor.adapters.kafka_consumer import KafkaConsumer
from financial_document_processor.adapters.kafka_producer import KafkaProducer
from financial_document_processor.config import get_settings
from financial_document_processor.domain.document import Document, DocumentStatus
from financial_document_processor.services.categorization import CategorizationService
from financial_document_processor.services.document_processor import DocumentProcessor
from financial_document_processor.services.file_decoder import FileDecoder
from financial_document_processor.services.parsers.bank_statement import BankStatementParser
from financial_document_processor.services.parsers.parser import DocumentParser
from financial_document_processor.utils.logging import setup_logging
from financial_document_processor.utils.metrics import setup_metrics

logger = logging.getLogger(__name__)


class Application:
    """
    Aplicação principal do processador de documentos financeiros.

    Coordena a inicialização e execução de todos os componentes.
    """

    def __init__(self):
        """Inicializa a aplicação."""
        self.settings = get_settings()

        setup_logging(self.settings.app.log_level)

        setup_metrics()

        self.repository = None
        self.kafka_consumer = None
        self.kafka_producer = None
        self.ai_provider = None
        self.file_decoder = None
        self.categorization_service = None
        self.document_processor = None
        self.parsers = {}

        # Flags de controle
        self.running = False
        self.shutdown_event = asyncio.Event()

    async def setup(self):
        """Configura e inicializa todos os componentes da aplicação."""
        logger.info("Inicializando aplicação...")

        try:
            self.repository = PostgresRepository(self.settings.database.url)
            await self.repository.connect()

            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.settings.kafka.bootstrap_servers,
                default_topic=self.settings.kafka.processed_topic
            )
            await self.kafka_producer.start()

            self.ai_provider = create_ai_provider(
                provider_name=self.settings.ai.provider,
                api_key=self._get_api_key_for_provider(),
                model=self._get_model_for_provider(),
                organization_id=self.settings.ai.openai_organization_id
            )
            logger.info(f"Usando provedor de IA: {self.settings.ai.provider}")

            self.file_decoder = FileDecoder(
                tesseract_path=self.settings.ocr.tesseract_path
            )

            self.parsers = self._setup_parsers()

            self.categorization_service = CategorizationService(
                ai_provider=self.ai_provider,
                predefined_categories=None,
                batch_size=self.settings.ai.batch_size,
                enable_caching=True
            )
            logger.info("Serviço de categorização inicializado")

            self.document_processor = DocumentProcessor(
                file_decoder=self.file_decoder,
                ai_provider=self.ai_provider,
                parsers=self.parsers,
                categorization_service=self.categorization_service
            )

            self.kafka_consumer = KafkaConsumer(
                bootstrap_servers=self.settings.kafka.bootstrap_servers,
                topic=self.settings.kafka.documents_topic,
                group_id=self.settings.kafka.consumer_group,
                message_handler=self.handle_document
            )
            await self.kafka_consumer.start()

            logger.info("Aplicação inicializada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar aplicação: {str(e)}")
            await self.shutdown()
            raise

    def _setup_parsers(self) -> Dict[str, DocumentParser]:
        """
        Configura os parsers para diferentes tipos de documentos.

        Returns:
            Dicionário de parsers por tipo de documento
        """
        return {
            "bank_statement": BankStatementParser(ai_provider=self.ai_provider),
        }

    def _get_api_key_for_provider(self) -> str:
        """
        Obtém a chave de API para o provedor configurado.

        Returns:
            Chave de API

        Raises:
            ValueError: Se a chave não estiver configurada
        """
        provider = self.settings.ai.provider.lower()

        if provider == "openai":
            if not self.settings.ai.openai_api_key:
                raise ValueError("Chave de API da OpenAI não configurada")
            return self.settings.ai.openai_api_key

        elif provider == "gemini":
            if not self.settings.ai.gemini_api_key:
                raise ValueError("Chave de API do Google Gemini não configurada")
            return self.settings.ai.gemini_api_key

        elif provider == "claude":
            if not self.settings.ai.claude_api_key:
                raise ValueError("Chave de API do Claude não configurada")
            return self.settings.ai.claude_api_key

        else:
            raise ValueError(f"Provedor não suportado: {provider}")

    def _get_model_for_provider(self) -> str:
        """
        Obtém o modelo para o provedor configurado.

        Returns:
            Nome do modelo
        """
        provider = self.settings.ai.provider.lower()

        if provider == "openai":
            return self.settings.ai.openai_model

        elif provider == "gemini":
            return self.settings.ai.gemini_model

        elif provider == "claude":
            return self.settings.ai.claude_model

        else:
            raise ValueError(f"Provedor não suportado: {provider}")

    async def handle_document(self, document: Document):
        """
        Processa um documento recebido do Kafka.

        Args:
            document: O documento a ser processado
        """
        logger.info(f"Processando documento {document.id} do tipo {document.document_type}")

        try:
            await self.repository.save_document(document)

            transactions = await self.document_processor.process(document)

            if transactions:
                await self.repository.save_transactions(transactions)

                await self.kafka_producer.send_message(
                    value={
                        "document_id": document.id,
                        "external_id": str(document.external_id),
                        "user_id": document.user_id,
                        "status": DocumentStatus.PROCESSED.value,
                        "transaction_count": len(transactions),
                        "processed_at": str(document.updated_at)
                    },
                    key=str(document.id)
                )

                await self.repository.update_document_status(
                    document_id=document.id,
                    status=DocumentStatus.PROCESSED
                )

                logger.info(
                    f"Documento {document.id} processado com sucesso. "
                    f"Extraídas {len(transactions)} transações."
                )

            else:
                logger.warning(f"Nenhuma transação extraída do documento {document.id}")

                await self.repository.update_document_status(
                    document_id=document.id,
                    status=DocumentStatus.PROCESSED
                )

                await self.kafka_producer.send_message(
                    value={
                        "document_id": document.id,
                        "external_id": str(document.external_id),
                        "user_id": document.user_id,
                        "status": DocumentStatus.PROCESSED.value,
                        "transaction_count": 0,
                        "processed_at": str(document.updated_at),
                        "message": "Nenhuma transação encontrada no documento"
                    },
                    key=str(document.id)
                )

        except Exception as e:
            logger.error(f"Erro ao processar documento {document.id}: {str(e)}")

            await self.repository.update_document_status(
                document_id=document.id,
                status=DocumentStatus.FAILED
            )

            await self.kafka_producer.send_message(
                value={
                    "document_id": document.id,
                    "external_id": str(document.external_id),
                    "user_id": document.user_id,
                    "status": DocumentStatus.FAILED.value,
                    "error": str(e),
                    "processed_at": str(document.updated_at)
                },
                key=str(document.id),
                topic=self.settings.kafka.processed_topic
            )

    async def run(self):
        """
        Executa a aplicação até receber sinal de shutdown.
        """
        if self.running:
            return

        self.running = True
        logger.info("Aplicação em execução")

        await self.shutdown_event.wait()

        await self.shutdown()

    async def shutdown(self):
        """
        Desliga todos os componentes da aplicação de forma ordenada.
        """
        if not self.running:
            return

        logger.info("Iniciando desligamento da aplicação...")
        self.running = False

        if self.kafka_consumer:
            await self.kafka_consumer.stop()

        if self.kafka_producer:
            await self.kafka_producer.stop()

        if self.repository:
            await self.repository.disconnect()

        logger.info("Aplicação desligada com sucesso")

    def handle_signals(self):
        """
        Configura handlers para sinais do sistema.
        """
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """
        Handler para sinais do sistema.

        Marca o evento de shutdown para iniciar o desligamento da aplicação.
        """
        logger.info(f"Sinal {sig} recebido, iniciando desligamento...")

        if not self.shutdown_event.is_set():
            self.shutdown_event.set()


async def main():
    """
    Função principal da aplicação.
    """
    app = Application()

    try:
        app.handle_signals()

        await app.setup()

        await app.run()

    except Exception as e:
        logger.error(f"Erro fatal na aplicação: {str(e)}")
        await app.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    """
    Ponto de entrada quando executado como script.
    """
    asyncio.run(main())