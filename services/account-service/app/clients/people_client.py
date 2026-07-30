"""HTTP client for people-service.

Replaces the monolith's in-process `validate_person` import.
Person validation is mandatory: when people-service is unreachable the caller
must fail the request rather than assume the person is valid.
"""

from typing import Optional

import httpx

from app.config import PEER_TIMEOUT_SECONDS, PEOPLE_SERVICE_URL, TENANT_ID
from app.logging_config import get_logger

logger = get_logger(__name__)


class PeopleServiceUnavailable(Exception):
    """Raised when people-service cannot be reached or returns an error."""


def validate_person(logon_id: str, correlation_id: Optional[str] = None) -> bool:
    """Return True when people-service confirms the person exists."""
    url = f"{PEOPLE_SERVICE_URL}/people/ValidatePerson"
    headers = {"X-Tenant-ID": TENANT_ID}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        response = httpx.get(
            url,
            params={"LogonId": logon_id},
            headers=headers,
            timeout=PEER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.error(
            "people_service_unavailable",
            extra={"logon_id": logon_id, "peer_url": url, "error": str(exc)},
        )
        raise PeopleServiceUnavailable(str(exc)) from exc

    return bool(payload.get("IsValid", False))
