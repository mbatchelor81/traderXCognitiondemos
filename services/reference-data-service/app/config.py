"""Configuration for Reference Data Service."""

import os
import sys

TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    print("FATAL: TENANT_ID environment variable is required.", file=sys.stderr)
    raise RuntimeError("TENANT_ID environment variable is required.")

SERVICE_NAME = "reference-data-service"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8004"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
