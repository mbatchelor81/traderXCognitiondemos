"""
FastAPI application entry point with Socket.io mount.
This is the main application module that wires everything together.
"""

import os

import sentry_sdk
import socketio
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.middleware import CorrelationIdMiddleware, RequestTimingMiddleware, TenantMiddleware
from app.routes import accounts, trades, positions, people, reference_data
from app.services.trade_processor import set_socketio_server
from app.utils.logging_config import configure_logging, get_logger

# =============================================================================
# Sentry SDK Initialization (must happen before app is created)
# =============================================================================
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=1.0,
        enable_logs=True,
    )

configure_logging(level=LOG_LEVEL)
logger = get_logger(__name__)

# =============================================================================
# Socket.io Server
# =============================================================================

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


# Set the Socket.io server reference in trade_processor
set_socketio_server(sio)

# =============================================================================
# FastAPI Application
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # Observability middleware (order matters: outermost runs first)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TenantMiddleware)

    # Include routers
    app.include_router(accounts.router, tags=["Accounts"])
    app.include_router(trades.router, tags=["Trades"])
    app.include_router(positions.router, tags=["Positions"])
    app.include_router(people.router, tags=["People"])
    app.include_router(reference_data.router, tags=["Reference Data"])

    @app.get("/")
    def root():
        return {
            "service": APP_TITLE,
            "version": APP_VERSION,
            "status": "running",
        }

    @app.get("/health")
    def health_check(db: Session = Depends(get_db)):
        """Health check with dependency verification."""
        checks = {}

        try:
            db.execute(text("SELECT 1"))
            checks["database"] = "connected"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"

        all_healthy = all(
            v in ("connected", "ok")
            for v in checks.values()
        )

        return JSONResponse(
            status_code=200 if all_healthy else 503,
            content={
                "status": "healthy" if all_healthy else "unhealthy",
                "checks": checks,
            },
        )

    @app.get("/sentry-debug")
    async def trigger_error():
        """Deliberately trigger an error for Sentry demo purposes."""
        division_by_zero = 1 / 0  # noqa: F841

    logger.info("FastAPI application created with all routes")
    return app


# Create the app instance
app = create_app()

# Mount Socket.io on the ASGI app
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
