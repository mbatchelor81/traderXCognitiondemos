"""Helpers copied from the monolith's app/utils/helpers.py, trimmed to what
account-service needs. Nothing is imported across service boundaries."""

from datetime import datetime, timezone

from app.config import TENANT_ID
from app.logging_config import get_logger

logger = get_logger(__name__)


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def get_tenant_from_request(request) -> str:
    """Return the tenant this instance serves."""
    return getattr(request.state, "tenant_id", TENANT_ID)


def get_correlation_id_from_request(request) -> str | None:
    """Return the correlation id assigned to this request, if any."""
    return getattr(request.state, "correlation_id", None)


def log_audit_event(event_type: str, tenant_id: str, **details) -> None:
    """Emit a structured audit log line."""
    logger.info(
        "audit_event",
        extra={"event_type": event_type, "audit_tenant_id": tenant_id, **details},
    )
