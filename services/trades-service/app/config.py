"""Configuration for Trades Service."""

import os

# Tenant Configuration (single-tenant mode)
TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    raise RuntimeError("TENANT_ID environment variable is required.")

# Database Configuration (tenant-specific by default)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# Reference Data Configuration
REFERENCE_DATA_FILE = os.getenv(
    "REFERENCE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "s-and-p-500-companies.csv")
)

# Application Configuration
APP_PORT = int(os.getenv("APP_PORT", "8002"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SERVICE_NAME = "trades-service"

# Socket.io Configuration
SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Inter-service URLs
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")

# Trade Processing Configuration
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# Tenant-specific Business Rules (loaded for current TENANT_ID only)
_ALL_TENANT_ALLOWED_SIDES = {
    "acme_corp": ["Buy", "Sell"],
    "globex_inc": ["Buy", "Sell"],
    "initech": ["Buy", "Sell"],
}

_ALL_TENANT_AUTO_SETTLE = {
    "acme_corp": True,
    "globex_inc": True,
    "initech": False,
}

TENANT_ALLOWED_SIDES = _ALL_TENANT_ALLOWED_SIDES.get(TENANT_ID, ["Buy", "Sell"])
TENANT_AUTO_SETTLE = _ALL_TENANT_AUTO_SETTLE.get(TENANT_ID, True)

# Audit Configuration
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
