"""
Prometheus metrics and OpenTelemetry tracing for account-service
(TARGET_ARCHITECTURE_CONSTRAINTS.md §10).

Metrics are served on ``/metrics`` and, because a single ALB fronts every
service, also on ``/svc/account/metrics``. ``/svc/account/health`` mirrors ``/health``
for the same reason: ``/health`` is ambiguous across services behind one
hostname, so each service owns an unambiguous gateway-scoped alias.

Tracing exports over OTLP when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set and is
otherwise inert — spans are created and propagated but never shipped anywhere.
"""

import os
import time
from typing import Callable, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import SERVICE_NAME, TENANT_ID
from app.logging_config import get_logger

logger = get_logger(__name__)

ROUTE_SLUG = "account"
GATEWAY_PREFIX = f"/svc/{ROUTE_SLUG}"

_LABELS = ("service", "tenant_id", "method", "path")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "HTTP requests handled, by outcome.",
    _LABELS + ("status",),
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    _LABELS,
)
REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "HTTP requests answered with a 4xx or 5xx status.",
    _LABELS + ("status",),
)
REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being served.",
    ("service", "tenant_id"),
)


def _route_template(request: Request) -> str:
    """The matched route template rather than the raw path, to bound cardinality."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request count, latency and error rate for every request."""

    async def dispatch(self, request: Request, call_next):
        in_progress = REQUESTS_IN_PROGRESS.labels(SERVICE_NAME, TENANT_ID)
        in_progress.inc()
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            in_progress.dec()
            labels = (SERVICE_NAME, TENANT_ID, request.method, _route_template(request))
            REQUEST_LATENCY.labels(*labels).observe(time.perf_counter() - start)
            REQUEST_COUNT.labels(*labels, str(status)).inc()
            if status >= 400:
                REQUEST_ERRORS.labels(*labels, str(status)).inc()


def metrics_endpoint() -> Response:
    """Prometheus exposition format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def register_observability(
    app: FastAPI, health_endpoint: Optional[Callable] = None
) -> None:
    """Install the metrics middleware, /metrics, and the gateway aliases."""
    app.add_middleware(MetricsMiddleware)

    for path in ("/metrics", f"{GATEWAY_PREFIX}/metrics"):
        app.add_api_route(
            path,
            metrics_endpoint,
            methods=["GET"],
            include_in_schema=False,
        )

    if health_endpoint is not None:
        app.add_api_route(
            f"{GATEWAY_PREFIX}/health",
            health_endpoint,
            methods=["GET"],
            include_in_schema=False,
        )


_tracing_configured = False


def configure_tracing(app: FastAPI) -> None:
    """Initialise OpenTelemetry and instrument inbound and outbound HTTP.

    ``traceparent`` headers are read from inbound requests and injected into
    outbound httpx calls, so a trade can be followed across service boundaries.
    """
    global _tracing_configured

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not _tracing_configured:
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": SERVICE_NAME,
                    "service.namespace": "traderx",
                    "deployment.environment": os.getenv("ENVIRONMENT", "local"),
                    "tenant.id": TENANT_ID,
                }
            )
        )
        if endpoint:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
            logger.info("tracing_exporter_configured", extra={"endpoint": endpoint})
        else:
            logger.info("tracing_exporter_disabled")
        trace.set_tracer_provider(provider)
        HTTPXClientInstrumentor().instrument()
        _tracing_configured = True

    FastAPIInstrumentor.instrument_app(
        app, excluded_urls="health,metrics,healthz"
    )
