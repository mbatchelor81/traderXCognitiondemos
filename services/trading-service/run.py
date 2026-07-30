"""
Entry point for the TraderX trading-service.
Usage: TENANT_ID=<tenant> python run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import HOST, LOG_LEVEL, PORT, SERVICE_NAME, TENANT_ID  # noqa: E402
from app.database import create_tables  # noqa: E402
from app.logging_config import configure_logging, get_logger  # noqa: E402
from app.seed import seed_database  # noqa: E402

configure_logging(LOG_LEVEL)
logger = get_logger(__name__)


def main() -> None:
    import uvicorn

    logger.info(
        "startup_begin",
        extra={"service": SERVICE_NAME, "tenant_id": TENANT_ID, "port": PORT},
    )

    create_tables()
    seed_database()

    config = uvicorn.Config(
        "app.main:combined_app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        lifespan="on",
        # Keep uvicorn's own loggers on the root JSON handler instead of its
        # default plain-text config.
        log_config=None,
    )
    # uvicorn's Server installs SIGTERM/SIGINT handlers that stop accepting new
    # connections, let in-flight requests drain, then run the app's shutdown
    # hook (which logs "shutting down") and re-raise the signal so the process
    # exits with the expected status.
    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()
