"""
Shared logging configuration for FastAPI, Celery, and MCP servers.
Uses loguru for structured logging with JSON support.
"""

import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Intercept standard logging calls and redirect to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record to loguru."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:  # type: ignore[union-attr]
            frame = frame.f_back  # type: ignore[union-attr]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """
    Configure logging for all server components.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output JSON-formatted logs (for production)
    """
    # Remove default loguru handler
    logger.remove()

    # Add new handler with format
    if json_logs:
        logger.add(
            sys.stderr,
            format="{time} {level} {message}",
            level=level,
            serialize=True,
        )
    else:
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(sys.stderr, format=fmt, level=level)

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
