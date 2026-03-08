"""
Tenant enforcement middleware for TraderX Monolith (single-tenant mode).
Enforces that all requests use the startup TENANT_ID.
Rejects requests with a mismatched X-Tenant-ID header with 403.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID


class TenantMiddleware(BaseHTTPMiddleware):
    """Enforces single-tenant mode. Rejects mismatched X-Tenant-ID headers."""

    async def dispatch(self, request: Request, call_next):
        header_tenant = request.headers.get("X-Tenant-ID")

        # Reject requests that specify a different tenant
        if header_tenant and header_tenant != TENANT_ID:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Tenant mismatch: this instance serves tenant '{TENANT_ID}', "
                              f"but request specified '{header_tenant}'."
                },
            )

        # Always set tenant to the startup TENANT_ID
        request.state.tenant_id = TENANT_ID
        response = await call_next(request)
        return response
