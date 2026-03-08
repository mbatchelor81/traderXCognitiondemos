"""Startup script for Users Service."""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

from app.config import APP_HOST, APP_PORT, LOG_LEVEL, TENANT_ID, SERVICE_NAME
from app.database import create_tables

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"'
           + SERVICE_NAME + '","tenant_id":"' + TENANT_ID
           + '","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


def main():
    import uvicorn

    logger.info("=" * 60)
    logger.info("TraderX Users Service — Starting Up")
    logger.info("TENANT_ID: %s", TENANT_ID)
    logger.info("Port: %d", APP_PORT)
    logger.info("=" * 60)

    logger.info("Creating database tables...")
    create_tables()
    logger.info("Database tables ready")

    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        log_level=LOG_LEVEL.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()
