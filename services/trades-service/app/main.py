"""FastAPI application entry point for Trades Service."""

import logging
import signal
import sys

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    TENANT_ID, SERVICE_NAME, CORS_ORIGINS, DEBUG, LOG_LEVEL,
    SOCKETIO_CORS_ALLOWED,
)
from app.middleware import TenantMiddleware
from app.observability import setup_observability
from app.routes import trades, positions, reference_data
from app.services.trade_processor import set_socketio_server

# Structured JSON logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"'
           + SERVICE_NAME + '","tenant_id":"' + TENANT_ID
           + '","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


def handle_sigterm(signum, frame):
    """Handle SIGTERM for graceful shutdown."""
    logger.info("Received SIGTERM, shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)

# Socket.io Server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=SOCKETIO_CORS_ALLOWED,
    logger=DEBUG,
    engineio_logger=False,
)


@sio.event
async def connect(sid, environ):
    logger.info("Socket.io client connected: %s", sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket.io client disconnected: %s", sid)


@sio.event
async def subscribe(sid, data):
    """Handle room subscription requests from the frontend."""
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.enter_room(sid, room)
        logger.info("Client %s subscribed to room: %s", sid, room)


@sio.event
async def unsubscribe(sid, data):
    """Handle room unsubscription requests."""
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.leave_room(sid, room)
        logger.info("Client %s unsubscribed from room: %s", sid, room)


set_socketio_server(sio)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TraderX Trades Service",
        version="1.0.0",
        description="Trades service: trade processing, positions, reference data, real-time updates",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(TenantMiddleware)

    app.include_router(trades.router, tags=["Trades"])
    app.include_router(positions.router, tags=["Positions"])
    app.include_router(reference_data.router, tags=["Reference Data"])

    @app.get("/health")
    def health():
        return {"status": "UP", "service": SERVICE_NAME, "tenant": TENANT_ID}

    setup_observability(app)

    logger.info("Trades service application created")
    return app


app = create_app()

# Mount Socket.io on the ASGI app
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
