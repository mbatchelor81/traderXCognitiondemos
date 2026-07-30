"""
Helpers copied from traderx-monolith/app/utils/helpers.py, trimmed to what
position-service needs. Nothing is imported across service directories.
"""

from datetime import datetime
from typing import Optional

from app.config import AUDIT_ENABLED, TENANT_ID
from app.logging_config import get_logger

logger = get_logger(__name__)


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime to ISO string, or return None."""
    if dt is None:
        return None
    return dt.isoformat()


def get_tenant_from_request(request) -> str:
    """Return the tenant this instance serves."""
    return getattr(request.state, "tenant_id", TENANT_ID)


def get_correlation_id(request) -> Optional[str]:
    """Return the correlation id attached to the request, if any."""
    return getattr(request.state, "correlation_id", None)


def log_audit_event(event_type: str, tenant_id: str, details: str) -> None:
    """Log an audit event."""
    if not AUDIT_ENABLED:
        return
    logger.info("audit_event", extra={
        "event_type": event_type,
        "tenant_id": tenant_id,
        "details": details,
    })


def log_position_event(account_id, security, action, tenant_id, extra="") -> None:
    """Log a position-specific event for the audit trail."""
    details = f"account_id={account_id} security={security} action={action} {extra}"
    log_audit_event("POSITION", tenant_id, details)


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
