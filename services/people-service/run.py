"""
Entry point for people-service.
Usage: TENANT_ID=<tenant> python run.py
"""

import os
import sys

# Ensure the service directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import HOST, LOG_LEVEL, PORT, TENANT_ID  # noqa: E402
from app.logging_config import configure_logging, get_logger  # noqa: E402

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    """Start uvicorn. Uvicorn installs its own SIGTERM/SIGINT handlers, which
    stop accepting connections, drain in-flight requests and then fire the
    FastAPI shutdown event before the process exits."""
    import uvicorn

    logger.info(
        "starting people-service",
        extra={"tenant_id": TENANT_ID, "host": HOST, "port": PORT},
    )

    server = uvicorn.Server(
        uvicorn.Config(
            "app.main:app",
            host=HOST,
            port=PORT,
            log_level=LOG_LEVEL.lower(),
            # Keep uvicorn's own records on the root JSON handler.
            log_config=None,
            timeout_graceful_shutdown=30,
        )
    )
    server.run()

    logger.info("people-service stopped", extra={"tenant_id": TENANT_ID})


if __name__ == "__main__":
    main()
