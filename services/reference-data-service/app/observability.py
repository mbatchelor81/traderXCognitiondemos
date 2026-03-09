"""Observability module — correlation IDs, Prometheus metrics, OpenTelemetry tracing."""

import logging
import os
import time
import uuid

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import TENANT_ID, SERVICE_NAME

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
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
    "Total HTTP errors (4xx and 5xx)",
    ["service", "tenant_id", "method", "path", "status"],
)


# ---------------------------------------------------------------------------
# OpenTelemetry tracing (no-op if OTEL_EXPORTER_OTLP_ENDPOINT is not set)
# ---------------------------------------------------------------------------
def init_tracing(app: FastAPI) -> None:
    """Initialise OpenTelemetry tracing if an exporter endpoint is configured."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.propagators.composite import CompositePropagator
        from opentelemetry.trace.propagation.tracecontext import (
            TraceContextTextMapPropagator,
        )

        resource = Resource.create(
            {
                "service.name": SERVICE_NAME,
                "tenant.id": TENANT_ID,
            }
        )
        provider = TracerProvider(resource=resource)

        if endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = OTLPSpanExporter(endpoint=endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "OpenTelemetry OTLP exporter configured",
                extra={
                    "tenant_id": TENANT_ID,
                    "service": SERVICE_NAME,
                    "endpoint": endpoint,
                },
            )

        trace.set_tracer_provider(provider)
        set_global_textmap(
            CompositePropagator([TraceContextTextMapPropagator()])
        )
        FastAPIInstrumentor.instrument_app(app)
        logger.info(
            "OpenTelemetry tracing initialised",
            extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME},
        )
    except ImportError:
        logger.info(
            "OpenTelemetry packages not installed — tracing disabled",
            extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME},
        )


# ---------------------------------------------------------------------------
# Correlation-ID + metrics middleware
# ---------------------------------------------------------------------------
class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Inject correlation_id into logs, record Prometheus metrics."""

    async def dispatch(self, request: Request, call_next):
        # Correlation ID: prefer traceparent > X-Request-ID > generate
        correlation_id = (
            request.headers.get("x-request-id")
            or request.headers.get("traceparent")
            or str(uuid.uuid4())
        )

        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start

        method = request.method
        path = request.url.path
        status = str(response.status_code)

        # Record Prometheus metrics
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
        ).observe(elapsed)
        if response.status_code >= 400:
            ERROR_COUNT.labels(
                service=SERVICE_NAME,
                tenant_id=TENANT_ID,
                method=method,
                path=path,
                status=status,
            ).inc()

        # Log the request with correlation_id
        logger.info(
            "HTTP %s %s %s %.3fs",
            method,
            path,
            status,
            elapsed,
            extra={
                "tenant_id": TENANT_ID,
                "service": SERVICE_NAME,
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "status": status,
                "duration": round(elapsed, 4),
            },
        )

        # Propagate correlation ID in response
        response.headers["X-Request-ID"] = correlation_id
        return response


# ---------------------------------------------------------------------------
# /metrics endpoint
# ---------------------------------------------------------------------------
def add_metrics_endpoint(app: FastAPI) -> None:
    """Register /metrics endpoint returning Prometheus text format."""

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


# ---------------------------------------------------------------------------
# Public helper — call once in create_app()
# ---------------------------------------------------------------------------
def setup_observability(app: FastAPI) -> None:
    """Wire up all observability concerns for *app*."""
    app.add_middleware(ObservabilityMiddleware)
    add_metrics_endpoint(app)
    init_tracing(app)
