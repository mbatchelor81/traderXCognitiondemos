"""
Entry point for position-service.
Usage: TENANT_ID=acme_corp python run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.config import HOST, LOG_LEVEL, PORT, TENANT_ID  # noqa: E402
from app.database import create_tables  # noqa: E402
from app.logging_config import configure_logging, get_logger  # noqa: E402
from app.seed import seed_database  # noqa: E402

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    """Create tables, seed on first start, then serve until SIGTERM/SIGINT."""
    import uvicorn

    logger.info("startup", extra={"tenant_id": TENANT_ID, "host": HOST, "port": PORT})

    create_tables()
    seeded = seed_database()
    logger.info("database_ready", extra={"seeded": seeded})

    # uvicorn installs its own SIGTERM/SIGINT handlers: it stops accepting new
    # connections, lets in-flight requests finish, fires the FastAPI shutdown
    # event ("shutting down") and exits cleanly. Reload is deliberately off so
    # signals reach the serving process directly.
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
