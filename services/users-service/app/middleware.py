"""
Tenant enforcement and correlation ID middleware for users-service.
Single-tenant mode: always uses the startup TENANT_ID.
"""

import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Enforces single-tenant mode and propagates correlation ID."""

    async def dispatch(self, request: Request, call_next):
        # Correlation ID: use incoming header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Tenant enforcement
        header_tenant = request.headers.get("X-Tenant-ID")
        if header_tenant and header_tenant != TENANT_ID:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Tenant mismatch: this instance serves '{TENANT_ID}', "
                              f"but request specified '{header_tenant}'."
                },
            )
        request.state.tenant_id = TENANT_ID

        # Log request with correlation ID
        logger.info(
            "Request %s %s correlation_id=%s",
            request.method,
            request.url.path,
            correlation_id,
        )

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
