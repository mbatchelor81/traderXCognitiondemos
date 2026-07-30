"""
Entry point for the TraderX Reference Data Service.
Usage: TENANT_ID=<tenant> python run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn  # noqa: E402

from app.config import HOST, LOG_LEVEL, PORT, SERVICE_NAME, TENANT_ID  # noqa: E402
from app.logging_config import configure_logging, get_logger  # noqa: E402

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    """Start uvicorn. Uvicorn's own SIGTERM/SIGINT handling drains in-flight
    requests and triggers the FastAPI shutdown event before exiting."""
    logger.info(
        "starting",
        extra={"service": SERVICE_NAME, "tenant_id": TENANT_ID, "host": HOST, "port": PORT},
    )
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        timeout_graceful_shutdown=30,
    )
    logger.info("stopped", extra={"service": SERVICE_NAME, "tenant_id": TENANT_ID})


if __name__ == "__main__":
    main()
