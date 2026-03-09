"""Test fixtures for Reference Data Service."""
import os

os.environ.setdefault("TENANT_ID", "test_tenant")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)
