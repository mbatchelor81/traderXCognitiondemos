"""Account Service configuration."""
import os
import sys

SERVICE_NAME = "account-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("ERROR: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

PEOPLE_SERVICE_URL = os.getenv("PEOPLE_SERVICE_URL", "http://localhost:8005")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
