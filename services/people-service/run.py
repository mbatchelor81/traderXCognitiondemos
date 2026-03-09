"""Startup script for People Service."""

import uvicorn
from app.config import SERVICE_PORT, LOG_LEVEL, TENANT_ID, SERVICE_NAME

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME} on port {SERVICE_PORT} for tenant {TENANT_ID}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level=LOG_LEVEL.lower(),
    )
