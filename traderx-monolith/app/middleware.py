"""
Middleware stack for TraderX Monolith.

Provides:
- TenantMiddleware: injects tenant_id from X-Tenant-ID header
- CorrelationIdMiddleware: generates/propagates a correlation ID per request
- RequestTimingMiddleware: logs request duration for every API call
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Injects tenant_id from X-Tenant-ID header, falls back to env var."""

    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID", CURRENT_TENANT)
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Generates or extracts a correlation ID per request."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs request duration for every API call."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("request_completed", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "tenant_id": getattr(request.state, "tenant_id", None),
            "correlation_id": getattr(request.state, "correlation_id", None),
        })
        return response
