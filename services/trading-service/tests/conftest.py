"""Test configuration for Trading Service."""
import os

# Set TENANT_ID before any app imports
os.environ.setdefault("TENANT_ID", "test_tenant")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import create_tables, engine, Base


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)
