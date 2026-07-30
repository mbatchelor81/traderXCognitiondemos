"""
Outbound client for reference-data-service (REFERENCE_DATA_SERVICE_URL, :8004).

Replaces the monolith's in-process CSV lookup of S&P 500 tickers.
"""

from app.clients.http_client import request_json
from app.config import REFERENCE_DATA_SERVICE_URL
from app.logging_config import get_logger

logger = get_logger(__name__)

SERVICE = "reference-data-service"


async def security_exists(ticker: str) -> bool:
    """Validate a ticker — GET /stocks/{ticker}; 404 means unknown ticker."""
    url = f"{REFERENCE_DATA_SERVICE_URL}/stocks/{ticker}"
    status_code, payload = await request_json("GET", SERVICE, url)

    if status_code == 404:
        logger.warning("security_not_found", extra={"security": ticker})
        return False
    if status_code >= 400:
        logger.warning(
            "security_lookup_rejected",
            extra={"security": ticker, "status_code": status_code},
        )
        return False

    company_name = payload.get("companyName") if isinstance(payload, dict) else None
    logger.info(
        "security_validated",
        extra={"security": ticker, "company_name": company_name},
    )
    return True
