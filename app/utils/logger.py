"""Structured logging setup using structlog + stdlib logging.

All application loggers should be obtained via ``get_logger()`` so that every
log record is automatically enriched with:

- ``timestamp``  — ISO-8601 UTC
- ``level``      — DEBUG / INFO / WARNING / ERROR / CRITICAL
- ``logger``     — dotted module name of the caller
- Any extra key-value pairs passed at call-site (e.g. ``trace_id``, ``intent``)

In production the renderer emits **one JSON line per event** which is easy to
ingest into Datadog, CloudWatch, Elastic, etc.

In test / development the renderer falls back to coloured key=value output so
the console stays readable.

Usage
-----
    from app.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("request_received", question=payload.question, trace_id=trace_id)
"""

import logging
import logging.config
import os
from typing import Any

import structlog


def _is_json_mode() -> bool:
    """Return True when LOG_FORMAT=json or when running in CI/production."""
    return os.getenv("LOG_FORMAT", "pretty").lower() == "json"


def setup_logging(log_level: str = "INFO") -> None:
    """Configure stdlib logging + structlog processors.

    Should be called **once** at application startup (``create_app``).
    Safe to call multiple times (idempotent).
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if _is_json_mode():
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Avoid duplicate handlers on repeated calls
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog BoundLogger bound to *name*.

    Prefer passing ``__name__`` so the logger path matches the module.
    """
    return structlog.get_logger(name)
