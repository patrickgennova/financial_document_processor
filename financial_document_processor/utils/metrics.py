import asyncio
import time
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import start_http_server

# Métricas globais
DOCUMENT_PROCESSED_COUNT = Counter(
    'document_processed_total',
    'Número total de documentos processados',
    ['document_type', 'status']
)

TRANSACTION_EXTRACTED_COUNT = Counter(
    'transaction_extracted_total',
    'Número total de transações extraídas',
    ['document_type']
)

PROCESSING_TIME = Histogram(
    'document_processing_seconds',
    'Tempo de processamento de documentos em segundos',
    ['document_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

AI_API_CALLS = Counter(
    'ai_api_calls_total',
    'Número total de chamadas para APIs de IA',
    ['provider', 'operation']
)

AI_TOKEN_USAGE = Counter(
    'ai_token_usage_total',
    'Número total de tokens usados em APIs de IA',
    ['provider', 'operation']
)

AI_COST = Counter(
    'ai_cost_usd_total',
    'Custo total em USD para APIs de IA',
    ['provider', 'operation']
)

DOCUMENT_QUEUE_SIZE = Gauge(
    'document_queue_size',
    'Tamanho atual da fila de documentos para processamento'
)


def setup_metrics(port: int = 8000):
    """
    Configura o servidor HTTP para expor métricas Prometheus.

    Args:
        port: Porta para o servidor HTTP de métricas
    """
    # Inicializa o servidor HTTP para expor métricas
    start_http_server(port)

    # Remove coletores padrão para métricas específicas da plataforma, se necessário
    # REGISTRY.unregister(PROCESS_COLLECTOR)
    # REGISTRY.unregister(PLATFORM_COLLECTOR)


def timing_metric(metric: Histogram):
    """
    Decorador para medir o tempo de execução de uma função e registrar no Prometheus.

    Args:
        metric: Histograma Prometheus para registrar o tempo

    Returns:
        Função decorada
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                execution_time = time.time() - start_time
                # Extrair labels apropriados do contexto, se necessário
                # Por exemplo, o tipo de documento poderia vir dos args
                metric.observe(execution_time)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                execution_time = time.time() - start_time
                metric.observe(execution_time)

        # Escolhe o wrapper apropriado com base no tipo da função
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_ai_usage(func):
    """
    Decorador para rastrear uso de APIs de IA.

    Registra o número de chamadas, tokens utilizados e custo estimado.

    Args:
        func: Função a ser decorada

    Returns:
        Função decorada
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extrai o nome do provedor da instância self
        self = args[0]  # Assume que o primeiro argumento é self
        provider = self.name

        # Infere a operação com base no nome da função
        operation = func.__name__

        # Incrementa o contador de chamadas
        AI_API_CALLS.labels(provider=provider, operation=operation).inc()

        # Executa a função
        result = await func(*args, **kwargs)

        # Registra o uso de tokens e custo
        if hasattr(result, 'tokens_used') and hasattr(result, 'cost'):
            AI_TOKEN_USAGE.labels(provider=provider, operation=operation).inc(result.tokens_used)
            AI_COST.labels(provider=provider, operation=operation).inc(result.cost)

        return result

    return wrapper
