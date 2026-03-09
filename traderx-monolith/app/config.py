"""
Configuration module for TraderX single-tenant deployment.

All tenant-specific configuration is injected via environment variables.
Each deployment instance serves exactly one tenant.
"""

import os

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///traderx.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# Socket.io Configuration
# =============================================================================
SOCKETIO_ADDRESS = os.getenv("SOCKETIO_ADDRESS", "http://localhost:8000")
SOCKETIO_ASYNC_MODE = "asgi"
SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

# =============================================================================
# Reference Data Configuration
# =============================================================================
REFERENCE_DATA_FILE = os.getenv(
    "REFERENCE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "s-and-p-500-companies.csv")
)

# =============================================================================
# People Data Configuration
# =============================================================================
PEOPLE_DATA_FILE = os.getenv(
    "PEOPLE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "people.json")
)

# =============================================================================
# Application Configuration
# =============================================================================
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_TITLE = "TraderX API"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Single-tenant TraderX trading platform backend"

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Trade Processing Configuration
# =============================================================================
TRADE_PROCESSING_DELAY_MS = int(os.getenv("TRADE_PROCESSING_DELAY_MS", "0"))
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# =============================================================================
# Per-Deployment Business Rules (injected via env vars)
# =============================================================================
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", "100"))
ALLOWED_SIDES = os.getenv("ALLOWED_SIDES", "Buy,Sell").split(",")
AUTO_SETTLE = os.getenv("AUTO_SETTLE", "true").lower() == "true"

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "traderx_audit.log")
