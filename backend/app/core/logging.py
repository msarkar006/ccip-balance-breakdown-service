"""
Structured logging configuration with PII masking and correlation ID support.
"""
import logging
import re
from typing import Any

import structlog


def mask_pii(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Mask PII fields in log output.

    Args:
        logger: Logger instance (unused)
        method_name: Log method name (unused)
        event_dict: Log event dictionary

    Returns:
        Modified event dictionary with masked PII
    """
    # Email masking pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Fields to mask
    sensitive_fields = ['email', 'password', 'token', 'secret', 'api_key']

    for key, value in event_dict.items():
        if isinstance(value, str):
            # Mask emails
            if '@' in value:
                event_dict[key] = re.sub(email_pattern, '***@***.***', value)
            # Mask sensitive fields
            if any(field in key.lower() for field in sensitive_fields):
                event_dict[key] = '***'
        elif isinstance(value, dict):
            # Recursively mask nested dictionaries
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, str) and '@' in nested_value:
                    value[nested_key] = re.sub(email_pattern, '***@***.***', nested_value)

    return event_dict


def configure_logging() -> None:
    """
    Configure structlog with correlation ID and PII masking.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            mask_pii,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
