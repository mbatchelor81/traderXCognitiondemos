"""Observability module — Prometheus metrics and OpenTelemetry tracing."""
import time
import os

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import Response

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from app.config import SERVICE_NAME, TENANT_ID

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
)
ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error responses (4xx and 5xx)",
    ["method", "endpoint", "status", "service", "tenant_id"],
)


def metrics_response() -> Response:
    """Return Prometheus-format metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# --- OpenTelemetry Tracing ---
def init_tracing() -> None:
    """Initialize OpenTelemetry tracing with W3C TraceContext propagation."""
    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "tenant.id": TENANT_ID,
        }
    )
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except ImportError:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    # No-op if no endpoint configured (spans are recorded but not exported)

    trace.set_tracer_provider(provider)
    set_global_textmap(CompositePropagator([TraceContextTextMapPropagator()]))


def get_tracer():
    """Return a tracer for the service."""
    return trace.get_tracer(SERVICE_NAME)
