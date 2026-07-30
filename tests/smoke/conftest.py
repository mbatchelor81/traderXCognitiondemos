"""
Shared fixtures for the TraderX smoke tests.

Every service sits behind a single gateway host on a disjoint path prefix — the
ALB in AWS, and the nginx `gateway` container in docker-compose locally — so the
whole suite runs against one base URL:

    SMOKE_TEST_URL=http://localhost:8000                 # docker compose
    SMOKE_TEST_URL=http://<alb-dns-name>                 # deployed
"""

import os

import httpx
import pytest

DEFAULT_URL = "http://localhost:8000"

SERVICES = [
    ("account-service", "account"),
    ("trading-service", "trading"),
    ("position-service", "position"),
    ("reference-data-service", "reference-data"),
    ("people-service", "people"),
]


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("SMOKE_TEST_URL", DEFAULT_URL).rstrip("/")


@pytest.fixture(scope="session")
def tenant_id() -> str:
    return os.environ.get("TENANT_ID", "acme_corp")


@pytest.fixture(scope="session")
def client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=30.0, follow_redirects=True) as c:
        yield c
