"""
FastAPI application factory for position-service.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

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
from app.database import get_db
from app.logging_config import configure_logging, get_logger
from app.middleware import (
    CorrelationIdMiddleware,
    RequestTimingMiddleware,
    TenantMiddleware,
)
from app.routes import positions

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log startup/shutdown so drains are visible to the orchestrator."""
    logger.info("service started", extra={"tenant_id": TENANT_ID})
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

    # Middleware runs in reverse registration order: correlation id is
    # established first, then timing, then tenant pinning.
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(positions.router, tags=["Positions"])

    @app.get("/", summary="Service banner")
    def root():
        return {
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "status": "running",
            "tenant": TENANT_ID,
        }

    @app.get("/health", summary="Health check with database connectivity probe")
    def health(db: Session = Depends(get_db)):
        """Return UP when the tenant database answers, 503 DOWN otherwise."""
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:
            logger.error("health_check_failed", extra={"error": str(exc)})
            return JSONResponse(
                status_code=503,
                content={
                    "status": "DOWN",
                    "service": SERVICE_NAME,
                    "tenant": TENANT_ID,
                },
            )
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    return app


logger.info("position-service starting in single-tenant mode", extra={
    "tenant_id": TENANT_ID,
})

app = create_app()
