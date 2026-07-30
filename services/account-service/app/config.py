"""
Configuration for account-service.

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
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///accounts_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# Application Configuration
# =============================================================================
SERVICE_NAME = "account-service"
APP_TITLE = "TraderX Account Service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Account CRUD, account-user membership, and account validation"
PORT = int(os.getenv("PORT", "8001"))
HOST = os.getenv("HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# =============================================================================
# Peer Service URLs (HTTP-only cross-service communication)
# =============================================================================
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")
TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://localhost:8002")
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")
REFERENCE_DATA_SERVICE_URL = os.getenv(
    "REFERENCE_DATA_SERVICE_URL", "http://localhost:8004"
)
PEOPLE_SERVICE_URL = os.getenv("PEOPLE_SERVICE_URL", "http://localhost:8005")

# Outbound call timeout for peer services, in seconds.
PEER_TIMEOUT_SECONDS = float(os.getenv("PEER_TIMEOUT_SECONDS", "2"))
