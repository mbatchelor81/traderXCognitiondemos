"""People Service — FastAPI application entry point."""

import logging
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger

from app.config import TENANT_ID, SERVICE_NAME, LOG_LEVEL, CORS_ORIGINS
from app.routes import people
from app.services.people_service import load_people

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
        title="People Service",
        version="1.0.0",
        description="Person directory and validation service",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(people.router, tags=["People"])

    @app.get("/health")
    def health():
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    load_people()
    logger.info("People Service started",
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    return app


app = create_app()


def _handle_sigterm(signum, frame):
    logger.info("Received SIGTERM, shutting down gracefully",
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)
