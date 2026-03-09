"""
Tenant enforcement middleware for TraderX Monolith.
Single-tenant mode: enforces TENANT_ID from startup config.
Rejects requests with mismatched X-Tenant-ID header (403).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID


class TenantMiddleware(BaseHTTPMiddleware):
    """Enforces single-tenant mode. Rejects mismatched tenant headers."""

    async def dispatch(self, request: Request, call_next):
        header_tenant = request.headers.get("X-Tenant-ID")
        if header_tenant and header_tenant != TENANT_ID:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Tenant mismatch: this instance serves tenant '{TENANT_ID}', "
                              f"but request specified '{header_tenant}'."
                },
            )
        request.state.tenant_id = TENANT_ID
        response = await call_next(request)
        return response
