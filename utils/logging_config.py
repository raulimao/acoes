import logging
import sys
import structlog
from typing import Any, Dict

def configure_logger():
    """
    Configure structured logging (JSON) for production.
    Replaces standard logging and print statements.
    """
    
    # Configure processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # JSON renderer for production
    if sys.stdout.isatty():
         # Pretty print for local development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON for production (Render/Cloud)
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Wrap standard logging to also use structlog
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    return structlog.get_logger()

# Global logger instance
logger = configure_logger()
