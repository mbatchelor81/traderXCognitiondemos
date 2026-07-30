"""Shared fixtures. TENANT_ID must be set before any app module is imported."""

import os
import sys

os.environ.setdefault("TENANT_ID", "test_tenant")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

TEST_TENANT = os.environ["TENANT_ID"]


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client
