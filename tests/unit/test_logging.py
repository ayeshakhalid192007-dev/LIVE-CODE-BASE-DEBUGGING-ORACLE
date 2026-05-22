"""Tests for logging configuration."""

import logging
from typing import Any

import pytest
import structlog

from git_debug_oracle.utils.logging import configure_logging, get_logger


def test_configure_logging_development_mode() -> None:
    """Test that development mode uses ConsoleRenderer."""
    configure_logging(log_level="INFO", development=True)

    # Get structlog configuration
    processors = structlog.get_config()["processors"]

    # Check that ConsoleRenderer is in processors
    has_console_renderer = any(
        isinstance(p, structlog.dev.ConsoleRenderer) for p in processors
    )
    assert has_console_renderer, "Development mode should use ConsoleRenderer"


def test_configure_logging_production_mode() -> None:
    """Test that production mode uses JSONRenderer."""
    configure_logging(log_level="INFO", development=False)

    # Get structlog configuration
    processors = structlog.get_config()["processors"]

    # Check that JSONRenderer is in processors
    has_json_renderer = any(
        isinstance(p, structlog.processors.JSONRenderer) for p in processors
    )
    assert has_json_renderer, "Production mode should use JSONRenderer"


def test_configure_logging_debug_level() -> None:
    """Test that DEBUG log level is set correctly."""
    configure_logging(log_level="DEBUG", development=True)

    # Get root logger level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_configure_logging_info_level() -> None:
    """Test that INFO log level is set correctly."""
    configure_logging(log_level="INFO", development=True)

    # Get root logger level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_configure_logging_warning_level() -> None:
    """Test that WARNING log level is set correctly."""
    configure_logging(log_level="WARNING", development=True)

    # Get root logger level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING


def test_configure_logging_error_level() -> None:
    """Test that ERROR log level is set correctly."""
    configure_logging(log_level="ERROR", development=True)

    # Get root logger level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.ERROR


def test_configure_logging_invalid_level() -> None:
    """Test that invalid log level raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        configure_logging(log_level="INVALID", development=True)

    error_msg = str(exc_info.value)
    assert "invalid" in error_msg.lower()


def test_get_logger_returns_bound_logger() -> None:
    """Test that get_logger returns a structlog BoundLogger or proxy."""
    configure_logging(log_level="INFO", development=True)

    logger = get_logger("test_module")

    # Check that logger has the expected methods (works with proxy or direct BoundLogger)
    assert hasattr(logger, "bind")
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")


def test_get_logger_with_context() -> None:
    """Test that get_logger can bind context."""
    configure_logging(log_level="INFO", development=True)

    logger = get_logger("test_module", request_id="123", user_id="456")

    # BoundLogger should have _context attribute with bound values
    assert hasattr(logger, "_context")


def test_logging_includes_timestamp() -> None:
    """Test that logging configuration includes timestamp processor."""
    configure_logging(log_level="INFO", development=True)

    processors = structlog.get_config()["processors"]

    # Check that TimeStamper is in processors
    has_timestamper = any(
        isinstance(p, structlog.processors.TimeStamper) for p in processors
    )
    assert has_timestamper, "Logging should include timestamp processor"


def test_logging_includes_stack_info() -> None:
    """Test that logging configuration includes stack info processor."""
    configure_logging(log_level="INFO", development=True)

    processors = structlog.get_config()["processors"]

    # Check that StackInfoRenderer is in processors
    has_stack_info = any(
        isinstance(p, structlog.processors.StackInfoRenderer) for p in processors
    )
    assert has_stack_info, "Logging should include stack info processor"


def test_logging_includes_exception_formatting() -> None:
    """Test that logging configuration includes exception formatting."""
    configure_logging(log_level="INFO", development=True)

    processors = structlog.get_config()["processors"]

    # Check that format_exc_info is in processors
    has_exc_formatter = any(
        p == structlog.processors.format_exc_info for p in processors
    )
    assert has_exc_formatter, "Logging should include exception formatting"
