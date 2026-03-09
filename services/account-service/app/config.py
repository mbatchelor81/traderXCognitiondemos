"""Configuration for Account Service."""

import os
import sys

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("FATAL: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

SERVICE_NAME = "account-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Inter-service URLs
PEOPLE_SERVICE_URL = os.getenv("PEOPLE_SERVICE_URL", "http://localhost:8005")
POSITION_SERVICE_URL = os.getenv("POSITION_SERVICE_URL", "http://localhost:8003")
