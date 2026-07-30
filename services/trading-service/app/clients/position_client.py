"""
Outbound client for position-service (POSITION_SERVICE_URL, default :8003).

The trading-service never stores positions; it asks position-service for the
current quantity and posts deltas to it.
"""

from typing import Optional

from app.clients.http_client import PeerServiceError, request_json
from app.config import POSITION_SERVICE_URL
from app.logging_config import get_logger

logger = get_logger(__name__)

SERVICE = "position-service"


async def get_position_quantity(account_id: int, security: str) -> int:
    """Current net quantity for an account/security — GET /positions/{account_id}."""
    url = f"{POSITION_SERVICE_URL}/positions/{account_id}"
    status_code, payload = await request_json("GET", SERVICE, url)

    if status_code == 404 or not isinstance(payload, list):
        return 0

    for position in payload:
        if isinstance(position, dict) and position.get("security") == security:
            return int(position.get("quantity") or 0)
    return 0


async def apply_position_delta(
    account_id: int, security: str, quantity_delta: int
) -> Optional[dict]:
    """
    Apply a position delta — POST /positions/apply.
    Returns the updated position as reported by position-service.
    """
    url = f"{POSITION_SERVICE_URL}/positions/apply"
    status_code, payload = await request_json(
        "POST",
        SERVICE,
        url,
        json_body={
            "accountId": account_id,
            "security": security,
            "quantityDelta": quantity_delta,
        },
    )

    if status_code >= 400:
        logger.error(
            "position_apply_rejected",
            extra={
                "account_id": account_id,
                "security": security,
                "quantity_delta": quantity_delta,
                "status_code": status_code,
            },
        )
        raise PeerServiceError(
            SERVICE, url, f"rejected the position delta with HTTP {status_code}"
        )

    logger.info(
        "position_applied",
        extra={
            "account_id": account_id,
            "security": security,
            "quantity_delta": quantity_delta,
        },
    )
    return payload if isinstance(payload, dict) else None
