"""
Trade-domain helpers, copied from the monolith's shared helpers module and
reduced to what the trading-service needs.
"""

from datetime import datetime
from typing import Optional

from app.config import (
    AUDIT_ENABLED,
    MAX_TRADE_QUANTITY,
    MIN_TRADE_QUANTITY,
    TENANT_ID,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Date/Time Helpers
# =============================================================================

def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime to ISO string, or return None."""
    if dt is None:
        return None
    return dt.isoformat()


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_trade_side(side: str) -> bool:
    """Validate that a trade side is either Buy or Sell."""
    return side in ("Buy", "Sell")


def validate_trade_quantity(quantity: int) -> bool:
    """Validate that trade quantity is within the allowed range."""
    return MIN_TRADE_QUANTITY <= quantity <= MAX_TRADE_QUANTITY


def validate_trade_state(state: str) -> bool:
    """Validate that a trade state is one of the allowed values."""
    return state in ("New", "Processing", "Settled", "Cancelled")


# =============================================================================
# Tenant Helpers
# =============================================================================

def get_tenant_from_request(request) -> str:
    """Return the tenant this instance serves."""
    return getattr(request.state, "tenant_id", TENANT_ID)


# =============================================================================
# Audit Logging Helpers
# =============================================================================

def log_audit_event(event_type: str, tenant_id: str, details: str) -> None:
    """Emit an audit event as a structured log line."""
    if not AUDIT_ENABLED:
        return
    logger.info(
        "audit_event",
        extra={"event_type": event_type, "tenant_id": tenant_id, "details": details},
    )


def log_trade_event(trade_id, account_id, action, tenant_id, extra="") -> None:
    """Log a trade-specific event for the audit trail."""
    details = f"trade_id={trade_id} account_id={account_id} action={action} {extra}"
    log_audit_event("TRADE", tenant_id, details)


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
