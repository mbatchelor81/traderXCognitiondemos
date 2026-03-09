"""FastAPI application entry point for trades-service."""

import logging
import signal
import sys

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import TENANT_ID, SERVICE_NAME, CORS_ORIGINS, SOCKETIO_CORS_ALLOWED, LOG_LEVEL
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


def _handle_sigterm(signum, frame):
    """Graceful shutdown on SIGTERM."""
    logger.info("Received SIGTERM, shutting down gracefully")
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)

# Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=SOCKETIO_CORS_ALLOWED)


@sio.event
async def connect(sid, environ):
    logger.info("Socket.IO client connected: %s", sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket.IO client disconnected: %s", sid)


@sio.event
async def subscribe(sid, data):
    """Subscribe a client to a topic (room)."""
    topic = data.get("topic") if isinstance(data, dict) else data
    if topic:
        await sio.enter_room(sid, topic)
        logger.info("Client %s subscribed to %s", sid, topic)


@sio.event
async def unsubscribe(sid, data):
    """Unsubscribe a client from a topic (room)."""
    topic = data.get("topic") if isinstance(data, dict) else data
    if topic:
        await sio.leave_room(sid, topic)
        logger.info("Client %s unsubscribed from %s", sid, topic)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TraderX Trades Service",
        version="1.0.0",
        description="Trades, positions, reference data, and real-time updates service",
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

    # Register Socket.IO with trade_processor
    set_socketio_server(sio)

    # Setup observability (metrics, tracing)
    setup_observability(app)

    logger.info("trades-service created for tenant: %s", TENANT_ID)
    return app


fastapi_app = create_app()

# Wrap FastAPI with Socket.IO ASGI app
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
