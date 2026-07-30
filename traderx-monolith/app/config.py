"""
Configuration module for TraderX.

The tenant this process serves is fixed at startup by the TENANT_ID environment
variable. There is no runtime tenant switching and no mutable tenant state.
"""

import os

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
# DATABASE_URL is overridable so production can point at a tenant-specific
# managed database; the default keeps each tenant in its own SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///traderx_{TENANT_ID}.db")
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
# Tenant Business Rules (injected per deployment, with defaults)
# =============================================================================
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", "50"))
ALLOWED_SIDES = [s.strip() for s in os.getenv("ALLOWED_SIDES", "Buy,Sell").split(",") if s.strip()]
AUTO_SETTLE = os.getenv("AUTO_SETTLE", "true").lower() == "true"

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "traderx_audit.log")
