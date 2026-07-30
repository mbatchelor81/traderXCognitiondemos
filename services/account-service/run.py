"""
Entry point for account-service.
Usage: TENANT_ID=<tenant> python run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn  # noqa: E402

from app.config import HOST, LOG_LEVEL, PORT, TENANT_ID  # noqa: E402
from app.database import create_tables  # noqa: E402
from app.logging_config import configure_logging, get_logger  # noqa: E402
from app.seed import seed_database  # noqa: E402

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    logger.info("startup_begin", extra={"tenant": TENANT_ID, "port": PORT})

    create_tables()
    seed_database()

    # uvicorn installs its own SIGTERM/SIGINT handlers: the server stops
    # accepting connections, in-flight requests drain, the FastAPI shutdown
    # event fires ("shutting down"), and the process exits cleanly.
    config = uvicorn.Config(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        timeout_graceful_shutdown=30,
        # Let uvicorn's own loggers propagate to the root JSON handler, and
        # leave request logging to RequestTimingMiddleware.
        log_config=None,
        access_log=False,
    )
    uvicorn.Server(config).run()

    logger.info("shutdown_complete", extra={"tenant": TENANT_ID})


if __name__ == "__main__":
    main()
