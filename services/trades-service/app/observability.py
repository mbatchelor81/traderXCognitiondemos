"""Observability module: Prometheus metrics, OpenTelemetry tracing, structured logging."""

import logging
import os
import time
import uuid

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.config import TENANT_ID, SERVICE_NAME

logger = logging.getLogger(__name__)

# ---- Prometheus Metrics ----

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["service", "tenant_id", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "tenant_id", "method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error count (4xx and 5xx)",
    ["service", "tenant_id", "method", "path", "status"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that records Prometheus metrics for every request."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path
        start_time = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start_time
        status = str(response.status_code)

        REQUEST_COUNT.labels(
            service=SERVICE_NAME,
            tenant_id=TENANT_ID,
            method=method,
            path=path,
            status=status,
        ).inc()

        REQUEST_LATENCY.labels(
            service=SERVICE_NAME,
            tenant_id=TENANT_ID,
            method=method,
            path=path,
        ).observe(duration)

        if response.status_code >= 400:
            ERROR_COUNT.labels(
                service=SERVICE_NAME,
                tenant_id=TENANT_ID,
                method=method,
                path=path,
                status=status,
            ).inc()

        return response


def add_metrics_endpoint(app: FastAPI) -> None:
    """Register the /metrics endpoint on the FastAPI app."""

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return StarletteResponse(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


# ---- Correlation ID Middleware ----

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Propagates or generates a correlation_id for each request."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-request-id")
            or str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


# ---- OpenTelemetry Tracing ----

def init_tracing(app: FastAPI) -> None:
    """Initialize OpenTelemetry tracing if an exporter endpoint is configured."""
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "tenant.id": TENANT_ID,
        })

        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "OpenTelemetry tracing enabled with OTLP exporter at %s",
                otlp_endpoint,
            )
        else:
            logger.info(
                "OpenTelemetry tracing initialized (no-op exporter — "
                "set OTEL_EXPORTER_OTLP_ENDPOINT to enable export)"
            )

        trace.set_tracer_provider(provider)

        # Instrument FastAPI (auto-propagates traceparent headers)
        FastAPIInstrumentor.instrument_app(app)
        # Instrument httpx (propagates traceparent on outbound calls)
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry instrumentation complete for %s", SERVICE_NAME)
    except Exception as exc:
        logger.warning("Failed to initialize OpenTelemetry tracing: %s", exc)


def setup_observability(app: FastAPI) -> None:
    """Wire up all observability features on the given FastAPI app."""
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(MetricsMiddleware)
    add_metrics_endpoint(app)
    init_tracing(app)
    logger.info("Observability stack initialized for %s", SERVICE_NAME)
