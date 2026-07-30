"""
Outbound client for account-service (ACCOUNT_SERVICE_URL, default :8001).

Replaces the monolith's direct queries against the accounts / account_users
tables from trade_processor.
"""

from typing import Any

from app.clients.http_client import request_json
from app.config import ACCOUNT_SERVICE_URL
from app.logging_config import get_logger

logger = get_logger(__name__)

SERVICE = "account-service"


def _exists_from_payload(payload: Any) -> bool:
    """account-service may answer with a bare bool or an {"exists": bool} body."""
    if isinstance(payload, bool):
        return payload
    if isinstance(payload, dict):
        for key in ("exists", "found"):
            if key in payload:
                return bool(payload[key])
    return True


async def account_exists(account_id: int) -> bool:
    """Check that the account exists — GET /account/{id}/exists."""
    url = f"{ACCOUNT_SERVICE_URL}/account/{account_id}/exists"
    status_code, payload = await request_json("GET", SERVICE, url)

    if status_code == 404:
        logger.warning("account_not_found", extra={"account_id": account_id})
        return False
    if status_code >= 400:
        logger.warning(
            "account_lookup_rejected",
            extra={"account_id": account_id, "status_code": status_code},
        )
        return False

    return _exists_from_payload(payload)


async def account_has_users(account_id: int) -> bool:
    """Check that the account has at least one user — GET /accountuser/?accountId=."""
    url = f"{ACCOUNT_SERVICE_URL}/accountuser/"
    status_code, payload = await request_json(
        "GET", SERVICE, url, params={"accountId": account_id}
    )

    if status_code >= 400:
        logger.warning(
            "account_users_lookup_rejected",
            extra={"account_id": account_id, "status_code": status_code},
        )
        return False

    users = payload if isinstance(payload, list) else []
    logger.info(
        "account_users_resolved",
        extra={"account_id": account_id, "user_count": len(users)},
    )
    return len(users) > 0
