"""
Logger setup module for instagram_cookie_updater.

Configures structured logging:
- INFO and below -> stdout
- WARNING and above -> stderr
- Unified format (plain or JSON)
- Dynamic log level via LOG_LEVEL env variable.
- Dynamic format via LOG_FORMAT env variable.
"""

import json
import logging
import os
import sys


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Helper to get a logger.

    - If name is None: uses caller's module name.
    - If name provided: uses that explicitly.

    Args:
        name (str | None): Logger name.
    Returns:
        logging.Logger: Configured logger instance.
    """
    if name is None:
        name = sys._getframe(1).f_globals.get("__name__", "__main__")
    return logging.getLogger(name)


def _stdout_filter(record: logging.LogRecord) -> bool:
    """Filter: allow only records below WARNING for stdout."""
    return record.levelno < logging.WARNING


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


def setup_logger() -> None:
    """
    Configure root logger. Safe to call multiple times (idempotent).
    """
    root_logger = logging.getLogger()

    # Determine log level
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    root_logger.setLevel(log_level)

    # Determine log format
    log_format = os.getenv("LOG_FORMAT", "plain").lower()

    if log_format == "json":
        formatter: logging.Formatter = JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(_stdout_filter)
    stdout_handler.setFormatter(formatter)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)

    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)
