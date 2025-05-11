import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable

import aiokafka
from pydantic import ValidationError

from financial_document_processor.domain.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


def normalize_datetime_fields(data: dict):
    """Normaliza os campos de datetime no dicionário de dados JSON."""

    if "created_at" in data and data["created_at"]:
        if isinstance(data["created_at"], str):
            dt = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        else:
            dt = data["created_at"]

        if dt.tzinfo is not None:
            data["created_at"] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    if "updated_at" in data and data["updated_at"]:
        if isinstance(data["updated_at"], str):
            dt = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        else:
            dt = data["updated_at"]

        if dt.tzinfo is not None:
            data["updated_at"] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    return data


class KafkaConsumer:
    """
    Consumidor Kafka para receber mensagens com documentos para processamento.
    """

    def __init__(
            self,
            bootstrap_servers: str,
            topic: str,
            group_id: str,
            message_handler: Callable[[Document], Any],
            auto_offset_reset: str = "earliest",
            max_poll_interval_ms: int = 300000,  # 5 minutos
            max_poll_records: int = 10
    ):
        """
        Inicializa o consumidor Kafka.

        Args:
            bootstrap_servers: Lista de servidores Kafka
            topic: Tópico a ser consumido
            group_id: ID do grupo de consumidores
            message_handler: Função para processar as mensagens recebidas
            auto_offset_reset: Política de reset de offset (earliest/latest)
            max_poll_interval_ms: Intervalo máximo entre polls (ms)
            max_poll_records: Número máximo de registros por poll
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.message_handler = message_handler
        self.auto_offset_reset = auto_offset_reset
        self.max_poll_interval_ms = max_poll_interval_ms
        self.max_poll_records = max_poll_records
        self.consumer = None
        self.running = False
        self.consumer_task = None

    async def start(self):
        """
        Inicia o consumidor Kafka e começa a processar mensagens.
        """
        if self.running:
            logger.warning("Consumidor Kafka já está em execução")
            return

        self.running = True

        self.consumer = aiokafka.AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=self.auto_offset_reset,
            max_poll_interval_ms=self.max_poll_interval_ms,
            max_poll_records=self.max_poll_records,
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None
        )

        await self.consumer.start()
        logger.info(f"Consumidor Kafka iniciado para o tópico {self.topic}")

        self.consumer_task = asyncio.create_task(self._consume())

    async def stop(self):
        """
        Para o consumidor Kafka.
        """
        if not self.running:
            return

        self.running = False

        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            await self.consumer.stop()

        logger.info("Consumidor Kafka parado")

    async def _consume(self):
        """
        Loop principal de consumo de mensagens.
        """
        try:
            async for message in self.consumer:
                try:
                    logger.debug(
                        f"Mensagem recebida: tópico={message.topic}, "
                        f"partição={message.partition}, offset={message.offset}"
                    )

                    await self._process_message(message)

                    await self.consumer.commit()

                except Exception as e:
                    logger.error(f"Erro ao processar mensagem: {str(e)}")

                if not self.running:
                    break

        except asyncio.CancelledError:
            logger.info("Tarefa de consumo cancelada")
            raise

        except Exception as e:
            logger.error(f"Erro no loop de consumo: {str(e)}")
            raise

    async def _process_message(self, message):
        """
        Processa uma mensagem recebida.

        Args:
            message: Mensagem do Kafka
        """
        start_time = time.time()

        try:
            data = message.value

            data['status'] = DocumentStatus.PROCESSING.value

            data = normalize_datetime_fields(data)

            try:
                document = Document(**data)

                await self.message_handler(document)

                processing_time = time.time() - start_time
                logger.info(
                    f"Mensagem processada em {processing_time:.2f}s: "
                    f"documento_id={document.id}, tipo={document.document_type}"
                )

            except ValidationError as e:
                logger.error(f"Erro de validação do documento: {str(e)}")

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")


