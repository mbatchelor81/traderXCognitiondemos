"""
Structured JSON logging for account-service.

Every line is a single JSON object on stdout containing at least timestamp,
level, message, service and tenant_id. The correlation id of the request being
served (when there is one) is attached automatically via a context variable.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import LOG_LEVEL, SERVICE_NAME, TENANT_ID

correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "asctime",
    "message",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Renders log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "tenant_id": TENANT_ID,
        }

        correlation_id = correlation_id_var.get()
        if correlation_id:
            payload["correlation_id"] = correlation_id

        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    for existing in list(root.handlers):
        root.removeHandler(existing)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger that emits structured JSON lines."""
    configure_logging()
    return logging.getLogger(name)


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Bind a correlation id to the current execution context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Return the correlation id bound to the current execution context."""
    return correlation_id_var.get()
