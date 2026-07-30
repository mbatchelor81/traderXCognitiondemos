"""
Structured JSON logging for the trading-service.

Every line is a single JSON object on stdout carrying at least `timestamp`,
`level`, `message`, `service` and `tenant_id`, plus the correlation id of the
request being served when there is one.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from app.config import LOG_LEVEL, SERVICE_NAME, TENANT_ID

correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)

_RESERVED_RECORD_KEYS = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "getMessage", "levelname", "levelno", "lineno", "module",
        "msecs", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "stacklevel", "taskName", "thread",
        "threadName", "message",
    }
)


def get_correlation_id() -> Optional[str]:
    """Return the correlation id of the request currently being served."""
    return correlation_id_var.get()


class ContextFilter(logging.Filter):
    """Stamps every record with the service, tenant and correlation id."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = SERVICE_NAME
        if not getattr(record, "tenant_id", None):
            record.tenant_id = TENANT_ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_KEYS:
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging(level: str = LOG_LEVEL) -> None:
    """Configure the root logger with JSON output. Call once at startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance. Drop-in replacement for logging.getLogger()."""
    return logging.getLogger(name)
