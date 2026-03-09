"""
Configuration for trades-service.
Single-tenant mode: TENANT_ID is required at startup.
"""

import os
import sys

SERVICE_NAME = "trades-service"

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("ERROR: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

APP_PORT = int(os.getenv("APP_PORT", "8002"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

REFERENCE_DATA_FILE = os.getenv(
    "REFERENCE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "s-and-p-500-companies.csv"),
)

# Trade processing config
TRADE_PROCESSING_DELAY_MS = int(os.getenv("TRADE_PROCESSING_DELAY_MS", "0"))
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# Tenant-specific business rules
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

# Inter-service URLs
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")
