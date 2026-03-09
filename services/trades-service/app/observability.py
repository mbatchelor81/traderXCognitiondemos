"""
Observability module for trades-service.
Provides Prometheus metrics, OpenTelemetry tracing, and metrics endpoint.
"""

import os
import time
import logging

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.config import SERVICE_NAME, TENANT_ID

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "tenant_id", "method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "tenant_id", "method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error responses (4xx and 5xx)",
    ["service", "tenant_id", "method", "path", "status"],
)


def init_tracing(app: FastAPI) -> None:
    """Initialize OpenTelemetry tracing if an OTLP endpoint is configured."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not otlp_endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set; tracing disabled (no-op)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "tenant.id": TENANT_ID,
        })
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        logger.info("OpenTelemetry tracing initialized, exporting to %s", otlp_endpoint)
    except Exception:
        logger.warning("Failed to initialize OpenTelemetry tracing", exc_info=True)


def setup_observability(app: FastAPI) -> None:
    """Wire Prometheus metrics middleware and /metrics endpoint into the app."""

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next) -> Response:
        """Record request count, latency, and error rate."""
        # Use the route template (e.g. /positions/{accountId}) instead of the
        # raw path to avoid unbounded Prometheus cardinality.
        route = request.scope.get("route")
        path = route.path if route else request.url.path
        method = request.method

        # Skip metrics endpoint itself
        if path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

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

        # Propagate correlation ID in response
        correlation_id = request.headers.get("X-Correlation-ID", "")
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id

        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        """Prometheus-compatible metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    # Initialize tracing
    init_tracing(app)

    logger.info("Observability initialized: /metrics endpoint, request metrics, tracing")
