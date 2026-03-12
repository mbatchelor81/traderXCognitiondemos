"""People Service configuration."""
import os
import sys

SERVICE_NAME = "people-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8005"))

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("ERROR: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
