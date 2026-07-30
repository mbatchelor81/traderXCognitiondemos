"""
Tenant enforcement middleware for TraderX.
Every request is served for the startup TENANT_ID; a request that names a
different tenant is rejected.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import *  # noqa: F401,F403 — intentional global config import


class TenantMiddleware(BaseHTTPMiddleware):
    """Pins every request to the startup tenant and rejects mismatched tenants."""

    async def dispatch(self, request: Request, call_next):
        requested_tenant = request.headers.get("X-Tenant-ID")
        if requested_tenant and requested_tenant != TENANT_ID:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": (
                        f"This instance serves tenant '{TENANT_ID}' only; "
                        f"'{requested_tenant}' was requested."
                    )
                },
            )

        request.state.tenant_id = TENANT_ID
        return await call_next(request)
