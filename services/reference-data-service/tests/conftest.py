"""Shared pytest fixtures. TENANT_ID must be set before any app import."""

import os
import sys

os.environ.setdefault("TENANT_ID", "test_tenant")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

TENANT_ID = os.environ["TENANT_ID"]


@pytest.fixture
def client():
    """TestClient that runs the startup event (loading the CSV catalogue)."""
    with TestClient(app) as test_client:
        yield test_client
