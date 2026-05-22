"""Logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog


def configure_logging(log_level: str, development: bool = True) -> None:
    """Configure structlog for development or production mode.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR)
        development: If True, use human-readable console output.
                    If False, use JSON output for production.

    Raises:
        ValueError: If log_level is not a valid log level string.
    """
    # Validate log level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
    if log_level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid log level: {log_level}. Must be one of {valid_levels}"
        )

    # Convert string to logging level constant
    numeric_level = getattr(logging, log_level.upper())

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Explicitly set root logger level (basicConfig only works on first call)
    logging.getLogger().setLevel(numeric_level)

    # Build processor chain
    processors: list[Any] = [
        # Add log level to event dict
        structlog.stdlib.add_log_level,
        # Add logger name to event dict
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exception info
        structlog.processors.format_exc_info,
    ]

    # Add renderer based on mode
    if development:
        # Human-readable console output with colors
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    else:
        # JSON output for production log aggregation
        processors.append(
            structlog.processors.JSONRenderer()
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger with optional initial context.

    Args:
        name: Logger name (typically module name)
        **initial_context: Key-value pairs to bind to logger context

    Returns:
        BoundLogger instance with initial context bound
    """
    logger = structlog.get_logger(name)

    if initial_context:
        logger = logger.bind(**initial_context)

    return logger
