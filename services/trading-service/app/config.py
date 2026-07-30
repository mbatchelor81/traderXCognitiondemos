"""
Configuration for the TraderX trading-service.

The tenant this process serves is fixed at startup by the TENANT_ID environment
variable. There is no runtime tenant switching and no mutable tenant state.
"""

import os

# =============================================================================
# Service Identity
# =============================================================================
SERVICE_NAME = "trading-service"
APP_TITLE = "TraderX Trading Service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "Trade submission, validation, state machine, analytics and the Socket.io "
    "trade feed for a single tenant."
)

# =============================================================================
# Tenant Configuration (immutable — resolved once at startup)
# =============================================================================
TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    raise RuntimeError(
        "TENANT_ID environment variable is required. "
        "Each instance serves exactly one tenant."
    )

# =============================================================================
# Database Configuration (one database per tenant)
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///trades_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# HTTP Server Configuration
# =============================================================================
PORT = int(os.getenv("PORT", "8002"))
HOST = os.getenv("HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Socket.io Configuration
# =============================================================================
SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

# =============================================================================
# Peer Services (HTTP only — no cross-service database access)
# =============================================================================
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")
REFERENCE_DATA_SERVICE_URL = os.getenv(
    "REFERENCE_DATA_SERVICE_URL", "http://localhost:8004"
)
PEER_REQUEST_TIMEOUT_SECONDS = float(os.getenv("PEER_REQUEST_TIMEOUT_SECONDS", "5"))

# =============================================================================
# Trade Processing Configuration
# =============================================================================
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# =============================================================================
# Tenant Business Rules (injected per deployment, with defaults)
# =============================================================================
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", "50"))
ALLOWED_SIDES = [
    s.strip() for s in os.getenv("ALLOWED_SIDES", "Buy,Sell").split(",") if s.strip()
]
AUTO_SETTLE = os.getenv("AUTO_SETTLE", "true").lower() == "true"

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
