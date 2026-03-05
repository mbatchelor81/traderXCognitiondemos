"""
Tenant injection middleware for TraderX Monolith.
Injects tenant_id from X-Tenant-ID header, falls back to env var.
"""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import *  # noqa: F401,F403 — intentional global config import

CURRENT_TENANT = os.getenv("DEFAULT_TENANT", "acme_corp")


class TenantMiddleware(BaseHTTPMiddleware):
    """Injects tenant_id from X-Tenant-ID header, falls back to env var."""

    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID", CURRENT_TENANT)
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response
