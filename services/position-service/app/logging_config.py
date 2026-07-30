"""
Structured JSON logging configuration for position-service.

Every line is a single JSON object on stdout including at least timestamp,
level, message, service and tenant_id.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from app.config import LOG_LEVEL, SERVICE_NAME, TENANT_ID

_RESERVED_RECORD_KEYS = frozenset({
    "name", "msg", "args", "created", "relativeCreated", "exc_info",
    "exc_text", "stack_info", "lineno", "funcName", "pathname", "filename",
    "module", "levelno", "levelname", "thread", "threadName", "process",
    "processName", "getMessage", "message", "msecs", "taskName",
})


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "tenant_id": TENANT_ID,
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_KEYS:
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging(level: str = LOG_LEVEL) -> None:
    """Configure the root logger with JSON formatting. Call once at startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance. Drop-in replacement for logging.getLogger()."""
    return logging.getLogger(name)
