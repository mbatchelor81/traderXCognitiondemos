"""FastAPI application entry point for users-service."""

import logging
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import TENANT_ID, SERVICE_NAME, CORS_ORIGINS, LOG_LEVEL

from app.middleware import TenantMiddleware
from app.routes import accounts, people

# Structured JSON logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"'
           + SERVICE_NAME + '","tenant_id":"' + TENANT_ID
           + '","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


def _handle_sigterm(signum, frame):
    """Graceful shutdown on SIGTERM."""
    logger.info("Received SIGTERM, shutting down gracefully")
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TraderX Users Service",
        version="1.0.0",
        description="Accounts, account-users, and people directory service",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(TenantMiddleware)

    app.include_router(accounts.router, tags=["Accounts"])
    app.include_router(people.router, tags=["People"])

    @app.get("/health")
    def health():
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    logger.info("users-service created for tenant: %s", TENANT_ID)
    return app


app = create_app()
