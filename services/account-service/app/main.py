"""FastAPI application factory for account-service."""

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
from app.routes import accounts

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("service_started", extra={"tenant": TENANT_ID})
    yield
    logger.info("shutting down", extra={"tenant": TENANT_ID})


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
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Added last => outermost, so the correlation id is bound before the
    # timing middleware and the tenant check run.
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(accounts.router, tags=["Accounts"])

    @app.get("/", summary="Service metadata")
    def root() -> dict:
        return {
            "service": SERVICE_NAME,
            "version": APP_VERSION,
            "status": "running",
            "tenant": TENANT_ID,
        }

    @app.get(
        "/health",
        summary="Liveness and database connectivity check",
        responses={
            200: {
                "description": "Service is up and the database is reachable",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "UP",
                            "service": SERVICE_NAME,
                            "tenant": TENANT_ID,
                        }
                    }
                },
            },
            503: {"description": "Database is unreachable"},
        },
    )
    def health(db: Session = Depends(get_db)):
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


logger.info(
    "account-service starting in single-tenant mode", extra={"tenant": TENANT_ID}
)

app = create_app()
