"""
Entry point for the TraderX Monolith application.
Usage: python run.py
"""

import logging
import sys
import os

# Ensure the monolith directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import APP_HOST, APP_PORT, DEBUG, LOG_LEVEL
from app.database import create_tables
from app.seed import seed_database

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    import uvicorn

    logger.info("=" * 60)
    logger.info("TraderX Monolith — Starting Up")
    logger.info("=" * 60)

    # Step 1: Create database tables if they don't exist
    logger.info("Creating database tables...")
    create_tables()
    logger.info("Database tables ready")

    # Step 2: Seed the database if empty
    logger.info("Checking if database needs seeding...")
    seeded = seed_database()
    if seeded:
        logger.info("Database seeded with sample data")
    else:
        logger.info("Database already populated")

    # Step 3: Start uvicorn
    logger.info("Starting uvicorn on %s:%d (debug=%s)", APP_HOST, APP_PORT, DEBUG)

    uvicorn.run(
        "app.main:combined_app",
        host=APP_HOST,
        port=APP_PORT,
        reload=DEBUG,
        log_level=LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
