"""
Logger setup module for instagram_cookie_updater.

Configures structured logging:
- INFO and below -> stdout
- WARNING and above -> stderr
- Unified format.
"""

import logging
import sys


def _stdout_filter(record: logging.LogRecord) -> bool:
    """Filter: allow only records below WARNING for stdout."""
    return record.levelno < logging.WARNING


def setup_logger() -> None:
    """
    Configure root logger. Safe to call multiple times (idempotent).
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear handlers if any
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
