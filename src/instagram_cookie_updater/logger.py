"""
Logger setup module for instagram_cookie_updater.

- INFO and below -> stdout
- WARNING and above -> stderr
- Unified format (plain or JSON).
- Single setup entrypoint: call setup_logger() only once from main.py.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone


def _stdout_filter(record: logging.LogRecord) -> bool:
    """Filter to allow only records below WARNING for stdout."""
    return record.levelno < logging.WARNING


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logs.

    Example output:
    {"timestamp": "2025-04-28T21:42:00Z", "level": "INFO", "module": "cookie_manager", "line": 42, "message": "..."}
    """

    def format(self, record: logging.LogRecord) -> str:
        record_dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="seconds") + "Z",
            "level": record.levelname,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        return json.dumps(record_dict)


class PlainFormatter(logging.Formatter):
    """
    Plain text formatter using ISO8601 timestamps, like JSON but readable.

    Example output:
    2025-04-28T21:42:00Z [INFO] cookie_manager:42 Starting refresh worker...
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="seconds") + "Z"

    def format(self, record: logging.LogRecord) -> str:
        record.asctime = self.formatTime(record)
        return f"{record.asctime} [{record.levelname}] {record.module}:{record.lineno} {record.getMessage()}"


def setup_logger() -> None:
    """
    Configure the root logger.

    Must be called once at app startup (e.g., in main.py).
    Safe to call multiple times but unnecessary.
    """
    log_format = os.getenv("LOG_FORMAT", "plain").lower()  # "plain" or "json"
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    formatter: logging.Formatter

    if log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = PlainFormatter()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

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


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Helper to get a logger for a module.

    Args:
        name: Module name. If None, automatically infer the caller's module name
              using sys._getframe(1).f_globals["__name__"].

    Returns:
        Configured logger instance.

    Example:
        logger = get_logger()
    """
    if name is None:
        name = sys._getframe(1).f_globals.get("__name__", "__main__")
    return logging.getLogger(name)
