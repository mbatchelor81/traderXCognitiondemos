"""Configuration for Trading Service."""

import os
import sys

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("FATAL: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

SERVICE_NAME = "trading-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8002"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

# Inter-service URLs
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8001")
REFERENCE_DATA_SERVICE_URL = os.getenv("REFERENCE_DATA_SERVICE_URL", "http://localhost:8004")
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")

# Trade processing config
TENANT_ALLOWED_SIDES = ["Buy", "Sell"]
TENANT_AUTO_SETTLE = os.getenv("TENANT_AUTO_SETTLE", "true").lower() == "true"
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
