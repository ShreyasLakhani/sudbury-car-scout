"""
Structured logging module for Car Scout.

Provides consistent, formatted logging across all components:
- Scraper (selenium crawling)
- API (FastAPI endpoints)
- DB operations

Outputs to both stdout (visible in Railway/Docker logs) and rotating file.
"""

import logging
import logging.handlers
import os
import sys


_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
_MAX_BYTES = 1_000_000  # 1 MB per log file
_BACKUP_COUNT = 3


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a named logger with stream + rotating file handlers.

    Args:
        name: Logger identifier (e.g. "api", "scraper", "db").
        level: Minimum log level. Defaults to INFO.

    Returns:
        Configured logger instance. Safe to call multiple times —
        duplicate handlers are prevented.
    """
    logger = logging.getLogger(f"carscout.{name}")

    # Avoid adding handlers twice if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # Don't bubble up to root logger

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # --- Stream handler (stdout) → visible in Railway / Docker logs ---
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # --- Rotating file handler → useful for local/self-hosted deployments ---
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(_LOG_DIR, f"{name}.log"),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # If we can't write to disk (e.g. read-only container), just skip
        logger.warning("Could not create file log handler for '%s'", name)

    return logger
