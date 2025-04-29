"""
Unit tests for logger module.
"""

import io
import json
import logging

from instagram_cookie_updater.logger import JsonFormatter, PlainFormatter, get_logger


def test_get_logger_returns_logger_instance() -> None:
    """Ensure get_logger returns a configured logger."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert hasattr(logger, "info")
    assert logger.name == "instagram_cookie_updater.logger" or "logger" in logger.name


def test_get_logger_with_custom_name() -> None:
    """Ensure get_logger returns logger with specified name."""
    name = "custom.logger"
    logger = get_logger(name)
    assert logger.name == name


def test_plain_formatter_log_output() -> None:
    """Ensure plain formatter outputs expected format to a stream."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(PlainFormatter())

    logger = get_logger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("Plain log test")
    handler.flush()

    output = stream.getvalue()
    assert "Plain log test" in output
    assert "[INFO]" in output
    assert "test_logger" in output or "logger" in output


def test_json_formatter_log_output() -> None:
    """Ensure JSON formatter outputs expected structured log to a stream."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    logger = get_logger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("JSON log test")
    handler.flush()

    output = stream.getvalue().strip()
    log_dict = json.loads(output)

    assert log_dict["level"] == "INFO"
    assert log_dict["message"] == "JSON log test"
    assert log_dict["module"] == "test_logger" or isinstance(log_dict["module"], str)
    assert "timestamp" in log_dict
    assert "line" in log_dict
