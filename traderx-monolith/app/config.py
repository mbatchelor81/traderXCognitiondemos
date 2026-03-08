"""
Global configuration module for TraderX Monolith.

WARNING: This module is imported by every other module using `from app.config import *`.
This is an intentional architectural smell — mutable global state shared everywhere.
"""

import os

# =============================================================================
# Tenant Configuration (single-tenant mode)
# =============================================================================
TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    raise RuntimeError("TENANT_ID environment variable is required.")

# =============================================================================
# Database Configuration (tenant-specific by default)
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# Socket.io Configuration
# =============================================================================
SOCKETIO_ADDRESS = os.getenv("SOCKETIO_ADDRESS", "http://localhost:8000")
SOCKETIO_ASYNC_MODE = "asgi"
SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

# =============================================================================
# Reference Data Configuration
# =============================================================================
REFERENCE_DATA_FILE = os.getenv(
    "REFERENCE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "s-and-p-500-companies.csv")
)

# =============================================================================
# People Data Configuration
# =============================================================================
PEOPLE_DATA_FILE = os.getenv(
    "PEOPLE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "people.json")
)

# =============================================================================
# Application Configuration
# =============================================================================
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_TITLE = "TraderX Monolith API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Monolithic backend replacing all TraderX microservices"

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Trade Processing Configuration
# =============================================================================
TRADE_PROCESSING_DELAY_MS = int(os.getenv("TRADE_PROCESSING_DELAY_MS", "0"))
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# =============================================================================
# Tenant-specific Business Rules (loaded for current TENANT_ID only)
# =============================================================================
_ALL_TENANT_MAX_ACCOUNTS = {
    "acme_corp": 100,
    "globex_inc": 50,
    "initech": 200,
}

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

# Resolve for current tenant at startup (with sensible defaults)
TENANT_MAX_ACCOUNTS = _ALL_TENANT_MAX_ACCOUNTS.get(TENANT_ID, 100)
TENANT_ALLOWED_SIDES = _ALL_TENANT_ALLOWED_SIDES.get(TENANT_ID, ["Buy", "Sell"])
TENANT_AUTO_SETTLE = _ALL_TENANT_AUTO_SETTLE.get(TENANT_ID, True)

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "traderx_audit.log")
