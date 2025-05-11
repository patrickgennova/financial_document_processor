import json
import logging
from typing import Any, Dict, Optional, Union

import aiokafka
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Produtor Kafka para enviar mensagens de resultado do processamento.
    """

    def __init__(
            self,
            bootstrap_servers: str,
            default_topic: Optional[str] = None,
            acks: str = "all",
            compression_type: str = "gzip"
    ):
        """
        Inicializa o produtor Kafka.

        Args:
            bootstrap_servers: Lista de servidores Kafka
            default_topic: Tópico padrão para envio (opcional)
            acks: Nível de confirmação de entrega (0, 1, all)
            compression_type: Tipo de compressão (none, gzip, snappy, lz4)
        """
        self.bootstrap_servers = bootstrap_servers
        self.default_topic = default_topic
        self.acks = acks
        self.compression_type = compression_type
        self.producer = None

    async def start(self):
        """
        Inicia o produtor Kafka.
        """
        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            acks=self.acks,
            compression_type=self.compression_type,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None
        )

        await self.producer.start()
        logger.info("Produtor Kafka iniciado")

    async def stop(self):
        """
        Para o produtor Kafka.
        """
        if self.producer:
            await self.producer.stop()
            logger.info("Produtor Kafka parado")

    async def send_message(
            self,
            value: Union[Dict[str, Any], BaseModel],
            key: Optional[Any] = None,
            topic: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None
    ):
        """
        Envia uma mensagem para o Kafka.

        Args:
            value: Valor da mensagem (dict ou modelo Pydantic)
            key: Chave da mensagem (opcional)
            topic: Tópico para envio, sobrescreve o padrão (opcional)
            headers: Cabeçalhos da mensagem (opcional)

        Raises:
            ValueError: Se nenhum tópico for especificado e não houver padrão
            Exception: Para erros durante o envio
        """
        if not self.producer:
            raise RuntimeError("Produtor não iniciado")

        target_topic = topic or self.default_topic
        if not target_topic:
            raise ValueError("Nenhum tópico especificado e não há tópico padrão")

        if isinstance(value, BaseModel):
            value_dict = value.model_dump()
        else:
            value_dict = value

        kafka_headers = None
        if headers:
            kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]

        try:
            result = await self.producer.send_and_wait(
                topic=target_topic,
                value=value_dict,
                key=key,
                headers=kafka_headers
            )

            logger.debug(
                f"Mensagem enviada: tópico={result.topic}, "
                f"partição={result.partition}, offset={result.offset}"
            )

            return result

        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o Kafka: {str(e)}")
            raise