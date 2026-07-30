"""
Configuration for the Reference Data Service.

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
# Service Identity
# =============================================================================
SERVICE_NAME = "reference-data-service"
APP_TITLE = "TraderX Reference Data Service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "S&P 500 reference data: ticker lookup and search."

# =============================================================================
# Reference Data Configuration
# =============================================================================
# Resolved relative to the service package so the process working directory
# does not matter.
REFERENCE_DATA_FILE = os.getenv(
    "REFERENCE_DATA_FILE",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "s-and-p-500-companies.csv",
    ),
)

# =============================================================================
# HTTP Server Configuration
# =============================================================================
PORT = int(os.getenv("PORT", "8004"))
HOST = os.getenv("HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Peer Service URLs
# =============================================================================
# This service makes no outbound calls today; the URLs are declared so that
# deployments configure every service identically.
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")
TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://localhost:8002")
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")
REFERENCE_DATA_SERVICE_URL = os.getenv(
    "REFERENCE_DATA_SERVICE_URL", "http://localhost:8004"
)
PEOPLE_SERVICE_URL = os.getenv("PEOPLE_SERVICE_URL", "http://localhost:8005")
