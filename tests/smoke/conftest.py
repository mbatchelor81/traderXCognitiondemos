"""Smoke test configuration — reads SMOKE_TEST_URL from environment."""

import os

import pytest
import httpx

SMOKE_TEST_URL = os.environ.get("SMOKE_TEST_URL", "http://localhost:8001")

# Service port mapping for direct-access mode (Docker Compose / port-forward)
SERVICE_PORTS = {
    "users-service": int(os.environ.get("USERS_SERVICE_PORT", "8001")),
    "trades-service": int(os.environ.get("TRADES_SERVICE_PORT", "8002")),
    "frontend": int(os.environ.get("FRONTEND_PORT", "80")),
}


@pytest.fixture(scope="session")
def base_url():
    """Base URL for smoke tests (ALB or localhost)."""
    return SMOKE_TEST_URL.rstrip("/")


@pytest.fixture(scope="session")
def users_url(base_url):
    """URL for users-service. Uses port mapping in direct mode."""
    if "localhost" in base_url or "127.0.0.1" in base_url:
        port = SERVICE_PORTS["users-service"]
        return f"http://localhost:{port}"
    return base_url


@pytest.fixture(scope="session")
def trades_url(base_url):
    """URL for trades-service. Uses port mapping in direct mode."""
    if "localhost" in base_url or "127.0.0.1" in base_url:
        port = SERVICE_PORTS["trades-service"]
        return f"http://localhost:{port}"
    return base_url


@pytest.fixture(scope="session")
def frontend_url(base_url):
    """URL for frontend. Uses port mapping in direct mode."""
    if "localhost" in base_url or "127.0.0.1" in base_url:
        port = SERVICE_PORTS["frontend"]
        return f"http://localhost:{port}"
    return base_url


@pytest.fixture(scope="session")
def http_client():
    """Shared httpx client for smoke tests."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        yield client
