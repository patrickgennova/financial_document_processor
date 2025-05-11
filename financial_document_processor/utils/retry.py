import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, Type, Union, List, TypeVar


logger = logging.getLogger(__name__)

# Tipo genérico para a função decorada
F = TypeVar('F', bound=Callable[..., Any])


def async_retry(
        max_retries: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        jitter: bool = True,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
):
    """
    Decorador para retry com backoff exponencial para funções assíncronas.

    Args:
        max_retries: Número máximo de tentativas
        min_wait: Tempo mínimo de espera entre tentativas (segundos)
        max_wait: Tempo máximo de espera entre tentativas (segundos)
        jitter: Se deve adicionar variação aleatória ao tempo de espera
        exceptions: Exceções que devem acionar o retry

    Returns:
        Função decorada com lógica de retry
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    if retry_count > 0:
                        logger.info(
                            f"Tentativa {retry_count}/{max_retries} para {func.__name__}"
                        )

                    return await func(*args, **kwargs)

                except exceptions as e:
                    retry_count += 1
                    last_exception = e

                    if retry_count > max_retries:
                        logger.error(
                            f"Máximo de {max_retries} tentativas excedido para {func.__name__}: {str(e)}"
                        )
                        raise

                    # Calcula o tempo de espera com backoff exponencial
                    wait_time = min(max_wait, min_wait * (2 ** (retry_count - 1)))

                    # Adiciona jitter se habilitado
                    if jitter:
                        wait_time = wait_time * (0.5 + random.random())

                    logger.warning(
                        f"Erro em {func.__name__}, tentativa {retry_count}/{max_retries}. "
                        f"Aguardando {wait_time:.2f}s antes de tentar novamente: {str(e)}"
                    )

                    # Aguarda antes da próxima tentativa
                    await asyncio.sleep(wait_time)

            # Este ponto só deveria ser alcançado se max_retries < 0
            if last_exception:
                raise last_exception
            return None  # Para satisfazer o type checker

        return wrapper  # type: ignore

    return decorator
