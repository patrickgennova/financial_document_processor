import logging
import time
from typing import Dict, List

from financial_document_processor.adapters.ai.ai_provider import AIProvider
from financial_document_processor.domain.document import Document
from financial_document_processor.domain.transaction import Transaction
from financial_document_processor.services.file_decoder import FileDecoder
from financial_document_processor.services.parsers.parser import DocumentParser

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Serviço principal para processamento de documentos financeiros.

    Coordena o fluxo completo de processamento, desde a decodificação do arquivo
    até a extração e categorização de transações.
    """

    def __init__(
            self,
            file_decoder: FileDecoder,
            ai_provider: AIProvider,
            parsers: Dict[str, DocumentParser],
            categorization_service=None
    ):
        """
        Inicializa o processador de documentos.

        Args:
            file_decoder: Instância do decodificador de arquivos
            ai_provider: Provedor de IA a ser utilizado
            parsers: Dicionário de parsers por tipo de documento
            categorization_service: Serviço de categorização (opcional)
        """
        self.file_decoder = file_decoder
        self.ai_provider = ai_provider
        self.parsers = parsers
        self.categorization_service = categorization_service

    async def process(self, document: Document) -> List[Transaction]:
        """
        Processa um documento, extraindo e categorizando transações.

        Args:
            document: Objeto Document a ser processado

        Returns:
            Lista de transações extraídas e categorizadas

        Raises:
            ValueError: Se o tipo de documento não for suportado
            Exception: Para outros erros durante o processamento
        """
        start_time = time.time()
        logger.info(
            f"Iniciando processamento do documento {document.id} "
            f"do tipo {document.document_type} para o usuário {document.user_id}"
        )

        try:
            if document.document_type not in self.parsers:
                raise ValueError(f"Tipo de documento não suportado: {document.document_type}")

            parser = self.parsers[document.document_type]

            text_content = self.file_decoder.decode_and_extract_text(
                document.file_content, document.content_type
            )

            if not text_content.strip():
                logger.warning(f"Nenhum texto extraído do documento {document.id}")
                return []

            transactions = await self.ai_provider.extract_transactions(
                text_content=text_content,
                document_type=document.document_type,
                predefined_categories=document.categories
            )

            if not transactions:
                logger.warning(f"Nenhuma transação extraída do documento {document.id}")
                return []

            for tx in transactions:
                tx.document_id = document.id
                tx.user_id = document.user_id

            processing_time = time.time() - start_time
            logger.info(
                f"Processamento do documento {document.id} concluído em {processing_time:.2f}s. "
                f"Extraídas {len(transactions)} transações."
            )

            return transactions

        except Exception as e:
            logger.error(f"Erro ao processar documento {document.id}: {str(e)}")
            raise