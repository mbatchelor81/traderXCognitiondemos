"""Observability module: Prometheus metrics, OpenTelemetry tracing, correlation IDs."""

import os
import time
import uuid
import logging

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import SERVICE_NAME, TENANT_ID

logger = logging.getLogger(__name__)

# --- Prometheus Metrics ---

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "tenant_id", "method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "tenant_id", "method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error responses (4xx and 5xx)",
    ["service", "tenant_id", "method", "path", "status_code"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to record Prometheus metrics for each request."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        start_time = time.time()

        response = await call_next(request)

        # Use route template (e.g. /account/{account_id}) instead of raw path
        # to avoid unbounded Prometheus label cardinality
        route = request.scope.get("route")
        path = route.path if route else request.url.path

        duration = time.time() - start_time
        status_code = str(response.status_code)

        REQUEST_COUNT.labels(
            service=SERVICE_NAME,
            tenant_id=TENANT_ID,
            method=method,
            path=path,
            status_code=status_code,
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
                status_code=status_code,
            ).inc()

        return response


# --- Correlation ID Middleware ---

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Propagates or generates a correlation ID for each request."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("traceparent")
            or str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


# --- OpenTelemetry Tracing ---

def init_tracing(app: FastAPI):
    """Initialize OpenTelemetry tracing. Uses OTLP exporter if endpoint is configured,
    otherwise defaults to no-op."""
    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "tenant.id": TENANT_ID,
        })

        provider = TracerProvider(resource=resource)

        if otel_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = OTLPSpanExporter(endpoint=otel_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry tracing enabled with OTLP exporter: %s", otel_endpoint)
        else:
            logger.info("OpenTelemetry tracing initialized (no-op exporter, no OTEL_EXPORTER_OTLP_ENDPOINT set)")

        trace.set_tracer_provider(provider)

        # Instrument FastAPI for automatic span creation
        FastAPIInstrumentor.instrument_app(app)

        # Instrument httpx for outbound call trace propagation
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry instrumentation complete for %s", SERVICE_NAME)

    except ImportError as e:
        logger.warning("OpenTelemetry packages not available, tracing disabled: %s", e)


# --- Metrics Endpoint ---

def add_metrics_endpoint(app: FastAPI):
    """Add /metrics endpoint exposing Prometheus-compatible metrics."""

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


def setup_observability(app: FastAPI):
    """Wire all observability into the FastAPI app."""
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(MetricsMiddleware)
    add_metrics_endpoint(app)
    init_tracing(app)
    logger.info("Observability setup complete for %s", SERVICE_NAME)
