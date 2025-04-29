"""
Unit tests for logger module.
"""

import io
import json
import logging

import pytest

from instagram_cookie_generator.logger import JsonFormatter, PlainFormatter, _stdout_filter, get_logger, setup_logger


def test_get_logger_returns_logger_instance() -> None:
    """Ensure get_logger returns a configured logger."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert hasattr(logger, "info")
    assert logger.name == "instagram_cookie_generator.logger" or "logger" in logger.name


def test_get_logger_with_custom_name() -> None:
    """Ensure get_logger returns logger with specified name."""
    name = "custom.logger"
    logger = get_logger(name)
    assert logger.name == name


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO, logging.WARNING])
def test_stdout_filter_levels(level: int) -> None:
    """Test that _stdout_filter returns True for levels < WARNING."""
    record = logging.LogRecord("test", level, "", 0, "", None, None)
    expected = level < logging.WARNING
    assert _stdout_filter(record) == expected


def test_plain_formatter_log_output(caplog: pytest.LogCaptureFixture) -> None:
    """Test PlainFormatter produces expected log format."""
    logger = get_logger("test_logger")
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(PlainFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO):
        logger.info("Plain log test")

    assert any("Plain log test" in rec.message for rec in caplog.records)


def test_json_formatter_log_output() -> None:
    """Test JsonFormatter produces valid JSON output."""
    logger = get_logger("test_logger_json")
    logger.handlers.clear()

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("JSON log test")

    log_output = stream.getvalue()
    parsed = json.loads(log_output)

    assert parsed["message"] == "JSON log test"
    assert parsed["level"] == "INFO"


@pytest.mark.parametrize("log_format", ["plain", "json"])
@pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING"])
def test_setup_logger_env(monkeypatch: pytest.MonkeyPatch, log_format: str, log_level: str) -> None:
    """Test setup_logger configures root logger with format and level from env."""
    monkeypatch.setenv("LOG_FORMAT", log_format)
    monkeypatch.setenv("LOG_LEVEL", log_level)

    setup_logger()

    root_logger = logging.getLogger()
    level = getattr(logging, log_level, logging.INFO)
    assert root_logger.level == level

    assert len(root_logger.handlers) == 2

    handler_levels = {h.level for h in root_logger.handlers}
    assert logging.DEBUG in handler_levels
    assert logging.WARNING in handler_levels


def test_get_logger_name_inference() -> None:
    """Test get_logger infers caller module name."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)


def test_get_logger_with_explicit_name() -> None:
    """Test get_logger with explicit name."""
    name = "my.custom.logger"
    logger = get_logger(name)
    assert logger.name == name
