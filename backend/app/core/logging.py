# Structured logging configuration

import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_logging(level: str = "INFO"):
    """Configure a root logger with JSON output for easier structured logs.
    The function can be called early in the application start‑up (e.g., in main.py).
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        timestamp=True,
    )
    log_handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(log_handler)
