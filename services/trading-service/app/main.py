"""
FastAPI application for the trading-service, with the Socket.io trade feed
mounted on the same ASGI app (as the monolith did).
"""

from contextlib import asynccontextmanager

import socketio
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ORIGINS,
    LOG_LEVEL,
    SERVICE_NAME,
    SOCKETIO_CORS_ALLOWED,
    TENANT_ID,
)
from app.database import get_db
from app.logging_config import configure_logging, get_logger
from app.middleware import (
    CorrelationIdMiddleware,
    RequestTimingMiddleware,
    TenantMiddleware,
)
from app.observability import configure_tracing, register_observability
from app.routes import analytics, trades
from app.services.trade_processor import set_socketio_server

configure_logging(LOG_LEVEL)
logger = get_logger(__name__)

logger.info("service_configured", extra={"tenant_id": TENANT_ID})

# =============================================================================
# Socket.io Server — one tenant per deployment, so no tenant query parameter
# =============================================================================

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=SOCKETIO_CORS_ALLOWED,
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid, environ):
    logger.info("socketio_client_connected", extra={"sid": sid})


@sio.event
async def disconnect(sid):
    logger.info("socketio_client_disconnected", extra={"sid": sid})


@sio.event
async def subscribe(sid, data):
    """Handle room subscription requests from the frontend."""
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.enter_room(sid, room)
        logger.info("socketio_subscribed", extra={"sid": sid, "room": room})


@sio.event
async def unsubscribe(sid, data):
    """Handle room unsubscription requests."""
    room = data if isinstance(data, str) else data.get("room", "")
    if room:
        await sio.leave_room(sid, room)
        logger.info("socketio_unsubscribed", extra={"sid": sid, "room": room})


set_socketio_server(sio)


# =============================================================================
# FastAPI Application
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    tenant: str


class ServiceInfoResponse(BaseModel):
    service: str
    version: str
    status: str
    tenant: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("service_started", extra={"tenant_id": TENANT_ID})
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

    # Middleware runs outermost-last-added: correlation id, then timing, then
    # the tenant guard.
    app.add_middleware(TenantMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(trades.router)
    app.include_router(analytics.router)

    @app.get("/", summary="Service information", response_model=ServiceInfoResponse)
    def root() -> ServiceInfoResponse:
        return ServiceInfoResponse(
            service=SERVICE_NAME,
            version=APP_VERSION,
            status="running",
            tenant=TENANT_ID,
        )

    @app.get(
        "/health",
        summary="Health check with database connectivity verification",
        response_model=HealthResponse,
        responses={503: {"description": "The trades database is unreachable"}},
    )
    def health(db: Session = Depends(get_db)):
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 — any DB failure means DOWN
            logger.error("health_check_failed", extra={"reason": str(exc)})
            return JSONResponse(
                status_code=503,
                content={
                    "status": "DOWN",
                    "service": SERVICE_NAME,
                    "tenant": TENANT_ID,
                },
            )
        return HealthResponse(status="UP", service=SERVICE_NAME, tenant=TENANT_ID)

    register_observability(app, health_endpoint=health)
    configure_tracing(app)

    return app


app = create_app()

# ASGI entrypoint: Socket.io feed plus the REST API
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
