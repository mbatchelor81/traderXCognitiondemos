"""Tenant enforcement middleware with observability."""
import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import TENANT_ID, SERVICE_NAME
from app.observability import REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header_tenant = request.headers.get("X-Tenant-ID")
        if header_tenant and header_tenant != TENANT_ID:
            return JSONResponse(
                status_code=403,
                content={"detail": f"Tenant mismatch: this instance serves '{TENANT_ID}', got '{header_tenant}'."},
            )
        request.state.tenant_id = TENANT_ID

        # Correlation ID: propagate from header or generate new
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("traceparent") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Metrics: track request count and latency
        method = request.method
        path = request.url.path
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        status = str(response.status_code)

        REQUEST_COUNT.labels(
            method=method, endpoint=path, status=status,
            service=SERVICE_NAME, tenant_id=TENANT_ID,
        ).inc()
        REQUEST_LATENCY.labels(
            method=method, endpoint=path,
            service=SERVICE_NAME, tenant_id=TENANT_ID,
        ).observe(duration)

        if response.status_code >= 400:
            ERROR_COUNT.labels(
                method=method, endpoint=path, status=status,
                service=SERVICE_NAME, tenant_id=TENANT_ID,
            ).inc()

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id

        # Structured log with correlation_id
        logger.info(
            "request",
            extra={
                "tenant_id": TENANT_ID,
                "service": SERVICE_NAME,
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "status": status,
                "duration_s": round(duration, 4),
            },
        )

        return response
