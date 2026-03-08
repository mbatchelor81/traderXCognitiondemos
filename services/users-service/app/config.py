"""Configuration for Users Service."""

import os

# Tenant Configuration (single-tenant mode)
TENANT_ID = os.environ.get("TENANT_ID")
if not TENANT_ID:
    raise RuntimeError("TENANT_ID environment variable is required.")

# Database Configuration (tenant-specific by default)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///app_{TENANT_ID}.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# People Data Configuration
PEOPLE_DATA_FILE = os.getenv(
    "PEOPLE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "people.json")
)

# Application Configuration
APP_PORT = int(os.getenv("APP_PORT", "8001"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SERVICE_NAME = "users-service"

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Inter-service URLs
TRADES_SERVICE_URL = os.getenv("TRADES_SERVICE_URL", "http://localhost:8002")

# Audit Configuration
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
