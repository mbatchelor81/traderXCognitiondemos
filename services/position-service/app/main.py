"""Position Service — FastAPI application entry point."""

import logging
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger

from app.config import TENANT_ID, SERVICE_NAME, LOG_LEVEL, CORS_ORIGINS
from app.database import create_tables
from app.routes import positions
from app.observability import setup_observability

# Structured JSON logging
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
formatter._required_fields.extend(["tenant_id", "service"])
log_handler.setFormatter(formatter)
logging.root.handlers = [log_handler]
logging.root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Position Service",
        version="1.0.0",
        description="Position tracking and management service",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(positions.router, tags=["Positions"])

    @app.get("/health")
    def health():
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    create_tables()
    setup_observability(app)
    logger.info("Position Service started",
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    return app


app = create_app()


def _handle_sigterm(signum, frame):
    logger.info("Received SIGTERM, shutting down gracefully",
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)
