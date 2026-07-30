"""FastAPI application factory for the Reference Data Service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ORIGINS,
    SERVICE_NAME,
    TENANT_ID,
)
from app.logging_config import configure_logging, get_logger
from app.middleware import (
    CorrelationIdMiddleware,
    RequestTimingMiddleware,
    TenantMiddleware,
)
from app.observability import configure_tracing, register_observability
from app.routes.reference_data import router as reference_data_router
from app.services import stocks_service

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ticker catalogue at startup; log a clean shutdown."""
    stocks_service.load_catalogue()
    logger.info(
        "service_started",
        extra={"stock_count": stocks_service.stock_count()},
    )
    yield
    logger.info("shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # Middleware runs outermost-last: correlation ID is established first, then
    # request timing, then tenant enforcement.
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(reference_data_router, tags=["Reference Data"])

    @app.get("/", summary="Service metadata")
    def root() -> dict:
        return {
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "status": "running",
            "tenant": TENANT_ID,
        }

    @app.get("/health", summary="Liveness and readiness probe")
    def health() -> dict:
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    register_observability(app, health_endpoint=health)
    configure_tracing(app)

    logger.info("application_created", extra={"tenant_id": TENANT_ID})
    return app


app = create_app()
