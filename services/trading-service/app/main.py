"""Trading Service — FastAPI application entry point with Socket.io."""

import logging
import signal
import sys

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger

from app.config import TENANT_ID, SERVICE_NAME, LOG_LEVEL, CORS_ORIGINS, SOCKETIO_CORS_ALLOWED
from app.database import create_tables
from app.routes import trades
from app.services.trade_processor import set_socketio_server
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

# Socket.io server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=SOCKETIO_CORS_ALLOWED,
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid, environ):
    logger.info("Socket.io client connected: %s", sid,
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})


@sio.event
async def disconnect(sid):
    logger.info("Socket.io client disconnected: %s", sid,
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})


@sio.event
async def subscribe(sid, data):
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.enter_room(sid, room)


@sio.event
async def unsubscribe(sid, data):
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.leave_room(sid, room)


set_socketio_server(sio)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trading Service",
        version="1.0.0",
        description="Trade submission, processing, and real-time trade feed",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(trades.router, tags=["Trades"])

    @app.get("/health")
    def health():
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    create_tables()
    setup_observability(app)
    logger.info("Trading Service started", extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    return app


app = create_app()

combined_app = socketio.ASGIApp(sio, other_asgi_app=app)


def _handle_sigterm(signum, frame):
    logger.info("Received SIGTERM, shutting down gracefully",
                extra={"tenant_id": TENANT_ID, "service": SERVICE_NAME})
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)
