"""Tenant, correlation-ID and request-timing middleware."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID
from app.logging_config import correlation_id_var, get_logger

logger = get_logger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


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


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propagates an X-Correlation-ID across the request and its log lines."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        token = correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(token)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code and duration for every request."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response
