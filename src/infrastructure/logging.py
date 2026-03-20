"""
Logging - Infrastructure Layer

Structured logging using structlog.
- JSON output in production for log aggregation
- Colored console in development for readability
- Request ID context propagation
"""
import logging
import sys
from typing import Any

import structlog

from src.infrastructure.config import settings


def configure_logging() -> None:
    """
    Configure structlog with environment-appropriate output.
    
    Production: JSON format for log aggregation systems
    Development: Colored console for readability
    """
    # Base processors for all environments
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Output renderer based on environment
    if settings.is_production:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            _get_log_level()
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib root logger to be quiet
    # (structlog wraps it, but we don't want duplicate output)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=_get_log_level(),
    )


def _get_log_level() -> int:
    """Determine log level from settings."""
    if settings.debug:
        return logging.DEBUG
    return logging.INFO


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        Configured structlog bound logger
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, user_id: str | None = None, path: str = "") -> None:
    """
    Bind request-scoped context variables to structlog.
    
    Call at the start of each request to ensure all log entries
    include the request ID and user info.
    
    Args:
        request_id: Unique identifier for this request
        user_id: Authenticated user ID (if any)
        path: Request path for correlation
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
    )
    if user_id:
        structlog.contextvars.bind_contextvars(user_id=user_id)
    if path:
        structlog.contextvars.bind_contextvars(path=path)
