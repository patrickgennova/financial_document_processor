import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Intercepta logs da biblioteca logging padrão e os redireciona para o loguru.
    """

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level: str = "INFO"):
    """
    Configura o sistema de logging com loguru.

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    for name in logging.root.manager.loggerDict.keys():
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Configura o loguru
    logger.remove()  # Remove o handler padrão

    # Adiciona o handler de console com formatação apropriada
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Adiciona um handler de arquivo para logs persistentes
    logger.add(
        "logs/financial_document_processor.log",
        rotation="100 MB",
        retention="14 days",
        level=log_level,
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Sistema de logging configurado com nível {log_level}")
