"""HTTP client for position-service.

Replaces the monolith's cross-domain query against the positions table.
Position data is best-effort: when position-service is unreachable the caller
gets an empty list rather than an error.
"""

from typing import Optional

import httpx

from app.config import PEER_TIMEOUT_SECONDS, POSITION_SERVICE_URL, TENANT_ID
from app.logging_config import get_logger

logger = get_logger(__name__)


def get_positions_for_account(
    account_id: int, correlation_id: Optional[str] = None
) -> list[dict]:
    """Fetch positions for an account. Returns [] if the peer call fails."""
    url = f"{POSITION_SERVICE_URL}/positions/{account_id}"
    headers = {"X-Tenant-ID": TENANT_ID}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        response = httpx.get(url, headers=headers, timeout=PEER_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.warning(
            "position_service_unavailable",
            extra={
                "account_id": account_id,
                "peer_url": url,
                "error": str(exc),
            },
        )
        return []

    if not isinstance(payload, list):
        logger.warning(
            "position_service_unexpected_payload",
            extra={"account_id": account_id, "peer_url": url},
        )
        return []

    return payload
