"""
Configuration for position-service.

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
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///positions_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# Application Configuration
# =============================================================================
SERVICE_NAME = "position-service"
PORT = int(os.getenv("PORT", "8003"))
HOST = os.getenv("HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_TITLE = "TraderX Position Service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Position tracking, queries, and recalculation for one tenant"

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Peer Service URLs
# =============================================================================
# position-service has no outbound dependencies; its own URL is published so
# peers and deployment tooling share a single default.
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
