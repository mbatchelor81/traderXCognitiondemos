"""
Observability module for users-service.
Provides Prometheus metrics, OpenTelemetry tracing, and correlation ID support.
"""

import os
import time
import logging

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import Response

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import extract, inject

from app.config import TENANT_ID, SERVICE_NAME

logger = logging.getLogger(__name__)

# --- Prometheus Metrics ---

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status", "service", "tenant_id"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "service", "tenant_id"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP errors (4xx and 5xx)",
    ["method", "endpoint", "status", "service", "tenant_id"],
)


# --- OpenTelemetry Tracing ---

def init_tracing(app):
    """Initialize OpenTelemetry tracing. Uses OTLP exporter if endpoint is configured."""
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "tenant.id": TENANT_ID,
    })

    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry OTLP exporter configured: %s", otlp_endpoint)
        except Exception as e:
            logger.warning("Failed to configure OTLP exporter: %s", e)
    else:
        logger.info("No OTEL_EXPORTER_OTLP_ENDPOINT set; tracing initialized with no-op exporter")

    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    logger.info("OpenTelemetry tracing initialized for %s", SERVICE_NAME)


# --- Metrics Endpoint ---

async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# --- Metrics Middleware ---

class MetricsMiddleware:
    """ASGI middleware that records Prometheus metrics for each request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        method = request.method
        path = request.url.path

        # Skip metrics endpoint itself
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500  # default in case of unhandled error

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            status_str = str(status_code)

            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=status_str,
                service=SERVICE_NAME,
                tenant_id=TENANT_ID,
            ).inc()

            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path,
                service=SERVICE_NAME,
                tenant_id=TENANT_ID,
            ).observe(duration)

            if status_code >= 400:
                ERROR_COUNT.labels(
                    method=method,
                    endpoint=path,
                    status=status_str,
                    service=SERVICE_NAME,
                    tenant_id=TENANT_ID,
                ).inc()
