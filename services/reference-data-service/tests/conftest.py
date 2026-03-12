"""Test configuration for Reference Data Service."""
import os

# Set TENANT_ID before any app imports
os.environ.setdefault("TENANT_ID", "test_tenant")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.service import load_stocks_from_csv


@pytest.fixture(autouse=True)
def load_data():
    """Ensure stock data is loaded before tests."""
    load_stocks_from_csv()


@pytest.fixture
def client():
    return TestClient(app)
