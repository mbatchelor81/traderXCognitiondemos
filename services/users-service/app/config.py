"""
Configuration for users-service.
Single-tenant mode: TENANT_ID is required at startup.
"""

import os
import sys

SERVICE_NAME = "users-service"

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("ERROR: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

APP_PORT = int(os.getenv("APP_PORT", "8001"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

PEOPLE_DATA_FILE = os.getenv(
    "PEOPLE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "people.json"),
)

# Inter-service URLs
TRADES_SERVICE_URL = os.getenv("TRADES_SERVICE_URL", "http://localhost:8002")
