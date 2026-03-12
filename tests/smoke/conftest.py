"""Smoke test configuration — reads SMOKE_TEST_URL from environment."""
import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the deployment under test.

    Set SMOKE_TEST_URL to the ALB/Ingress URL or localhost for Docker Compose.
    Defaults to http://localhost:18094 (React frontend default port).
    """
    return os.environ.get("SMOKE_TEST_URL", "http://localhost:18094").rstrip("/")
