"""
FastAPI application factory for people-service.

people-service is stateless: the person directory is a static JSON file loaded
once at startup. Each process serves exactly one tenant.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
from app.routes import people
from app.services import people_service

configure_logging()
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Liveness/readiness payload."""

    status: str
    service: str
    tenant: str


class RootResponse(BaseModel):
    """Service identity payload."""

    service: str
    version: str
    status: str
    tenant: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    directory = people_service.load_directory()
    logger.info(
        "service_started",
        extra={"person_count": len(directory), "tenant_id": TENANT_ID},
    )
    yield
    logger.info("shutting down", extra={"tenant_id": TENANT_ID})


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

    # Added innermost-first: correlation id wraps timing, which wraps tenant.
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(people.router, tags=["People"])

    @app.get("/", response_model=RootResponse, summary="Service identity")
    def root() -> RootResponse:
        return RootResponse(
            service=SERVICE_NAME,
            version=APP_VERSION,
            status="running",
            tenant=TENANT_ID,
        )

    @app.get("/health", response_model=HealthResponse, summary="Health check")
    def health() -> HealthResponse:
        return HealthResponse(status="UP", service=SERVICE_NAME, tenant=TENANT_ID)

    logger.info("app_created", extra={"tenant_id": TENANT_ID})
    return app


app = create_app()
