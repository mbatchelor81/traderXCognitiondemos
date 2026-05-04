"""
Global configuration module for TraderX Monolith.

WARNING: This module is imported by every other module using `from app.config import *`.
This is an intentional architectural smell — mutable global state shared everywhere.
"""

import os

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///traderx.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# Tenant Configuration (mutable global state — intentional smell)
# =============================================================================
CURRENT_TENANT = os.getenv("DEFAULT_TENANT", "acme_corp")
DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", "acme_corp")

# This list is modified at runtime when new tenants are encountered
KNOWN_TENANTS = ["acme_corp", "globex_inc", "initech"]

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
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_TITLE = "TraderX Monolith API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Monolithic backend replacing all TraderX microservices"

# =============================================================================
# CORS Configuration
# =============================================================================
# Production should use an explicit origin allowlist via CORS_ORIGINS env var
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Trade Processing Configuration
# =============================================================================
TRADE_PROCESSING_DELAY_MS = int(os.getenv("TRADE_PROCESSING_DELAY_MS", "0"))
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# =============================================================================
# Tenant-specific Business Rules (intentional smell — config as business logic)
# =============================================================================
TENANT_MAX_ACCOUNTS = {
    "acme_corp": 100,
    "globex_inc": 50,
    "initech": 200,
}

TENANT_ALLOWED_SIDES = {
    "acme_corp": ["Buy", "Sell"],
    "globex_inc": ["Buy", "Sell"],
    "initech": ["Buy", "Sell"],
}

TENANT_AUTO_SETTLE = {
    "acme_corp": True,
    "globex_inc": True,
    "initech": False,
}

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "traderx_audit.log")

# =============================================================================
# Mutable Runtime State (intentional smell)
# =============================================================================
_runtime_state = {
    "total_trades_processed": 0,
    "last_trade_timestamp": None,
    "active_sessions": 0,
    "startup_time": None,
}


def get_runtime_state():
    """Get mutable runtime state dict."""
    return _runtime_state


def update_runtime_state(key, value):
    """Update mutable runtime state — called from various modules."""
    _runtime_state[key] = value


def set_current_tenant(tenant_id):
    """Mutate the global CURRENT_TENANT — intentional smell."""
    global CURRENT_TENANT
    CURRENT_TENANT = tenant_id
    if tenant_id not in KNOWN_TENANTS:
        KNOWN_TENANTS.append(tenant_id)
