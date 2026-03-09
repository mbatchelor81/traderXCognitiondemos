"""Smoke test configuration — reads SMOKE_TEST_URL from environment."""

import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL for smoke tests.

    Defaults to http://localhost:8001 (account-service) when running locally.
    Set SMOKE_TEST_URL to the ALB URL for live deployment testing.
    """
    return os.environ.get("SMOKE_TEST_URL", "http://localhost:8001").rstrip("/")


@pytest.fixture(scope="session")
def service_ports() -> dict:
    """Map of service names to their ports for local Docker Compose testing."""
    return {
        "account-service": 8001,
        "trading-service": 8002,
        "position-service": 8003,
        "reference-data-service": 8004,
        "people-service": 8005,
    }
