"""Smoke test configuration — reads SMOKE_TEST_URL from environment."""

import os

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL for smoke tests (default: http://localhost:8080)."""
    return os.environ.get("SMOKE_TEST_URL", "http://localhost:8080").rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str) -> httpx.Client:
    """Provide a shared httpx client for the test session."""
    with httpx.Client(base_url=base_url, timeout=30.0) as c:
        yield c
