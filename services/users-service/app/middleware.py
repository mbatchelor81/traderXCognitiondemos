"""
Tenant enforcement middleware for users-service.
Single-tenant mode: always uses the startup TENANT_ID.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID


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
        response = await call_next(request)
        return response
