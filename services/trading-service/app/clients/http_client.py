"""
Shared outbound HTTP plumbing for peer service calls.

Every call carries the tenant header and the correlation id of the inbound
request so a trade can be traced end to end across services.
"""

from typing import Any, Optional, Tuple

import httpx

from app.config import PEER_REQUEST_TIMEOUT_SECONDS, TENANT_ID
from app.logging_config import get_correlation_id, get_logger

logger = get_logger(__name__)


class PeerServiceError(Exception):
    """Raised when a peer service is unreachable or answers unusably."""

    def __init__(self, service: str, url: str, reason: str):
        self.service = service
        self.url = url
        self.reason = reason
        super().__init__(f"{service} unavailable ({url}): {reason}")


def _headers() -> dict:
    headers = {"X-Tenant-ID": TENANT_ID}
    correlation_id = get_correlation_id()
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return headers


async def request_json(
    method: str,
    service: str,
    url: str,
    *,
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
) -> Tuple[int, Any]:
    """
    Perform an HTTP call against a peer service.

    Returns (status_code, parsed_json_or_None). Raises PeerServiceError when the
    peer cannot be reached, times out, or returns a 5xx response.
    """
    try:
        async with httpx.AsyncClient(timeout=PEER_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.request(
                method, url, params=params, json=json_body, headers=_headers()
            )
    except httpx.HTTPError as exc:
        logger.error(
            "peer_service_unreachable",
            extra={"peer_service": service, "url": url, "reason": str(exc)},
        )
        raise PeerServiceError(service, url, str(exc)) from exc

    if response.status_code >= 500:
        logger.error(
            "peer_service_error_response",
            extra={
                "peer_service": service,
                "url": url,
                "status_code": response.status_code,
            },
        )
        raise PeerServiceError(
            service, url, f"responded with HTTP {response.status_code}"
        )

    try:
        payload = response.json()
    except ValueError:
        payload = None

    logger.debug(
        "peer_service_call",
        extra={
            "peer_service": service,
            "url": url,
            "status_code": response.status_code,
        },
    )
    return response.status_code, payload
