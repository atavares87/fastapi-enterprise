"""
Structured Logging Configuration

This module sets up structured logging using structlog for better
observability and debugging in production environments.
"""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.types import EventDict

from app.core.config import get_settings


def add_app_context(
    _logger: Any, _method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add application context to log entries.

    Args:
        logger: Logger instance
        method_name: Log method name
        event_dict: Event dictionary

    Returns:
        Enhanced event dictionary with app context
    """
    settings = get_settings()
    event_dict["app"] = settings.APP_NAME
    event_dict["version"] = "0.1.0"
    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with appropriate processors, formatters,
    and log levels based on application settings.
    """
    settings = get_settings()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Processors for log entries
    processors = [
        # Add application context to all log entries
        add_app_context,
        # Add timestamp
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        # Add caller information in debug mode
        (
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
            if settings.DEBUG
            else lambda logger, method_name, event_dict: event_dict
        ),
        # Stack trace for exceptions
        structlog.processors.format_exc_info,
        # Process stack info
        structlog.processors.StackInfoRenderer(),
    ]

    # Add appropriate renderer based on format
    # For ELK stack, always use JSON format for better indexing
    if (
        settings.LOG_FORMAT.lower() == "json"
        or os.getenv("ELK_ENABLED", "false").lower() == "true"
    ):
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
