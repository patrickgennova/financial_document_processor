"""
Testes de integração para os adaptadores Kafka.
"""
import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from financial_document_processor.adapters.kafka_consumer import KafkaConsumer
from financial_document_processor.adapters.kafka_producer import KafkaProducer
from financial_document_processor.domain.document import Document


class MockAIOKafkaConsumer:
    """Mock para o AIOKafkaConsumer."""

    def __init__(self, *topics, **kwargs):
        self.topics = topics
        self.messages = []
        self.started = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.started = False

    def add_message(self, topic, key, value):
        """Adiciona uma mensagem para consumo nos testes."""
        self.messages.append(MagicMock(
            topic=topic,
            partition=0,
            offset=len(self.messages),
            key=key,
            value=value
        ))

    async def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            # Simula o comportamento de espera do Kafka
            await asyncio.sleep(0.1)
            raise StopAsyncIteration

        return self.messages.pop(0)

    async def commit(self):
        pass


class MockAIOKafkaProducer:
    """Mock para o AIOKafkaProducer."""

    def __init__(self, **kwargs):
        self.sent_messages = []
        self.started = False

    async def start(self):
        self.started = True

    async def stop(self):
        self.started = False

    async def send_and_wait(self, topic, value, key=None, headers=None):
        """Simula o envio de uma mensagem."""
        message = MagicMock(
            topic=topic,
            partition=0,
            offset=len(self.sent_messages),
            key=key,
            value=value,
            headers=headers
        )
        self.sent_messages.append(message)
        return message


@pytest.fixture
def mock_kafka_consumer():
    """Cria um mock para o consumidor Kafka."""
    with patch('aiokafka.AIOKafkaConsumer', MockAIOKafkaConsumer):
        consumer = KafkaConsumer(
            bootstrap_servers="localhost:9092",
            topic="test-topic",
            group_id="test-group",
            message_handler=AsyncMock()
        )
        yield consumer


@pytest.fixture
def mock_kafka_producer():
    """Cria um mock para o produtor Kafka."""
    with patch('aiokafka.AIOKafkaProducer', MockAIOKafkaProducer):
        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            default_topic="test-topic"
        )
        yield producer


@pytest.mark.asyncio
async def test_kafka_consumer_start_stop(mock_kafka_consumer):
    """Testa iniciar e parar o consumidor Kafka."""
    # Inicializa o consumidor
    await mock_kafka_consumer.start()

    # Verifica se o consumidor foi iniciado
    assert mock_kafka_consumer.consumer.started

    # Para o consumidor
    await mock_kafka_consumer.stop()

    # Verifica se o consumidor foi parado
    assert not mock_kafka_consumer.consumer.started


@pytest.mark.asyncio
async def test_kafka_producer_start_stop(mock_kafka_producer):
    """Testa iniciar e parar o produtor Kafka."""
    # Inicializa o produtor
    await mock_kafka_producer.start()

    # Verifica se o produtor foi iniciado
    assert mock_kafka_producer.producer.started

    # Para o produtor
    await mock_kafka_producer.stop()

    # Verifica se o produtor foi parado
    assert not mock_kafka_producer.producer.started


@pytest.mark.asyncio
async def test_kafka_producer_send_message(mock_kafka_producer):
    """Testa o envio de mensagens pelo produtor Kafka."""
    # Inicializa o produtor
    await mock_kafka_producer.start()

    # Cria uma mensagem de teste
    message = {
        "id": 12345,
        "status": "processed",
        "transaction_count": 5
    }

    # Envia a mensagem
    await mock_kafka_producer.send_message(
        value=message,
        key="12345"
    )

    # Verifica se a mensagem foi enviada
    assert len(mock_kafka_producer.producer.sent_messages) == 1
    sent_message = mock_kafka_producer.producer.sent_messages[0]
    assert sent_message.topic == "test-topic"
    assert sent_message.key == "12345"
    assert sent_message.value == message

    # Para o produtor
    await mock_kafka_producer.stop()


@pytest.mark.asyncio
async def test_kafka_consumer_process_message(mock_kafka_consumer):
    """Testa o processamento de mensagens pelo consumidor Kafka."""
    # Define um handler de mensagens
    message_handler = AsyncMock()
    mock_kafka_consumer.message_handler = message_handler

    # Inicializa o consumidor
    await mock_kafka_consumer.start()

    # Adiciona uma mensagem para consumo
    document_data = {
        "id": 12345,
        "external_id": str(uuid.uuid4()),
        "user_id": 98765,
        "document_type": "bank_statement",
        "filename": "extrato_teste.txt",
        "content_type": "text/plain",
        "file_content": "base64_content",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Adiciona a mensagem ao consumidor
    mock_kafka_consumer.consumer.add_message(
        topic="test-topic",
        key="12345",
        value=document_data
    )

    # Executa o consumidor por um curto período
    consumer_task = asyncio.create_task(mock_kafka_consumer._consume())
    await asyncio.sleep(0.5)  # Tempo suficiente para processar a mensagem

    # Cancela a tarefa de consumo
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    # Verifica se o handler foi chamado com os parâmetros corretos
    message_handler.assert_called_once()
    assert isinstance(message_handler.call_args[0][0], Document)
    assert message_handler.call_args[0][0].id == 12345

    # Para o consumidor
    await mock_kafka_consumer.stop()


@pytest.mark.asyncio
async def test_kafka_error_handling(mock_kafka_consumer):
    """Testa o tratamento de erros no consumidor Kafka."""
    # Define um handler que lança exceção
    error_handler = AsyncMock(side_effect=ValueError("Erro de teste"))
    mock_kafka_consumer.message_handler = error_handler

    # Inicializa o consumidor
    await mock_kafka_consumer.start()

    # Adiciona uma mensagem para consumo
    document_data = {
        "id": 12345,
        "external_id": str(uuid.uuid4()),
        "user_id": 98765,
        "document_type": "bank_statement",
        "filename": "extrato_teste.txt",
        "content_type": "text/plain",
        "file_content": "base64_content",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Adiciona a mensagem ao consumidor
    mock_kafka_consumer.consumer.add_message(
        topic="test-topic",
        key="12345",
        value=document_data
    )

    # Executa o consumidor por um curto período
    consumer_task = asyncio.create_task(mock_kafka_consumer._consume())
    await asyncio.sleep(0.5)  # Tempo suficiente para processar a mensagem

    # Cancela a tarefa de consumo
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    # Verifica se o handler foi chamado
    error_handler.assert_called_once()

    # Para o consumidor
    await mock_kafka_consumer.stop()