import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(log_path: str | None = None, log_level=logging.INFO) -> logging.Logger:
    """
    Configura y devuelve un logger rotativo para el servidor HTTP.

    :param log_path: Ruta al archivo de log. Si es None, se usa 'server.log'.
    :param log_level: Nivel de log (por defecto INFO).
    :return: Logger configurado.
    """
    if log_path is None:
        log_path = "server.log"

    # Asegurar que el directorio exista
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("http_learning_server")
    logger.setLevel(log_level)

    # Evitar handlers duplicados si se llama dos veces
    if not logger.handlers:
        # Handler de archivo con rotación
        file_handler = RotatingFileHandler(
            log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        logger.info("Logger initialized (file: %s)", log_path)

    return logger
