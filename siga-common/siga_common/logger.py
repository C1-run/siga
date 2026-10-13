"""Structured logging for siga packages."""

import logging
import sys
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def configure_root(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """Configure the root logger.

    Args:
        level: Logging level for root
        log_file: Optional file path to also log to
    """
    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    root.addHandler(handler)

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
            root.addHandler(file_handler)
        except Exception:
            pass  # best-effort file logging
