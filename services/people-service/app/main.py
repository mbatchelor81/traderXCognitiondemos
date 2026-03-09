"""People Service FastAPI application."""
import logging
import signal
import sys
from pythonjsonlogger import jsonlogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import TENANT_ID, SERVICE_NAME, CORS_ORIGINS, LOG_LEVEL
from app.middleware import TenantMiddleware
from app.routes import router
from app.service import load_people_from_json
from app.observability import metrics_response, init_tracing

# Structured JSON logging
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
log_handler.setFormatter(formatter)
logging.root.handlers = [log_handler]
logging.root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="People Service", version="1.0.0", description="Provides people directory lookups")

    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(TenantMiddleware)
    app.include_router(router, tags=["People"])

    @app.get("/health")
    def health():
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    @app.get("/metrics")
    def metrics():
        return metrics_response()

    @app.on_event("startup")
    def on_startup():
        init_tracing()
        load_people_from_json()
        logger.info("People Service started", extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})

    return app


app = create_app()


def _sigterm_handler(signum, frame):
    logger.info("Received SIGTERM, shutting down gracefully", extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    sys.exit(0)

signal.signal(signal.SIGTERM, _sigterm_handler)
