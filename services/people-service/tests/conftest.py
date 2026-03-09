"""Test configuration for People Service."""
import os

# Set TENANT_ID before any app imports
os.environ.setdefault("TENANT_ID", "test_tenant")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.service import load_people_from_json


@pytest.fixture(autouse=True)
def load_data():
    """Ensure people data is loaded before tests."""
    load_people_from_json()


@pytest.fixture
def client():
    return TestClient(app)
