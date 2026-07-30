"""
Configuration for people-service.

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
# Application Configuration
# =============================================================================
SERVICE_NAME = "people-service"
APP_TITLE = "TraderX People Service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Person directory and person validation for TraderX"

PORT = int(os.getenv("PORT", "8005"))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# People Data Configuration
# =============================================================================
# Resolved relative to the service package so the process working directory
# does not matter.
PEOPLE_DATA_FILE = os.getenv(
    "PEOPLE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "people.json"),
)

# =============================================================================
# Peer Service URLs (people-service currently makes no outbound calls)
# =============================================================================
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")
TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://localhost:8002")
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")
REFERENCE_DATA_SERVICE_URL = os.getenv("REFERENCE_DATA_SERVICE_URL", "http://localhost:8004")
PEOPLE_SERVICE_URL = os.getenv("PEOPLE_SERVICE_URL", "http://localhost:8005")

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]
