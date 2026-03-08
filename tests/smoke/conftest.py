"""Smoke test configuration. Reads SMOKE_TEST_URL from the environment."""

import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL for the deployed application (ALB URL)."""
    url = os.environ.get("SMOKE_TEST_URL", "http://localhost")
    # Strip trailing slash for consistency
    return url.rstrip("/")
