"""Smoke test configuration — reads SMOKE_TEST_URL from environment."""

import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        default=os.environ.get("SMOKE_TEST_URL", "http://localhost"),
        help="Base URL for smoke tests (default: SMOKE_TEST_URL env or http://localhost)",
    )


@pytest.fixture
def base_url(request):
    """Return the base URL for all smoke test requests."""
    return request.config.getoption("--base-url").rstrip("/")
