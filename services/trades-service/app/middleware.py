"""
Tenant enforcement middleware for trades-service.
Single-tenant mode: always uses the startup TENANT_ID.
"""

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Enforces single-tenant mode using the startup TENANT_ID."""

    async def dispatch(self, request: Request, call_next):
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

        # Propagate or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
