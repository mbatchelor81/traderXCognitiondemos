"""Test configuration for Position Service."""
import os

# Set TENANT_ID before any app imports
os.environ.setdefault("TENANT_ID", "test_tenant")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import create_tables, engine, Base
from app.models import Position
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seed_positions():
    """Seed some positions for testing."""
    from app.database import SessionLocal
    from datetime import datetime
    db = SessionLocal()
    try:
        db.add(Position(account_id=1, tenant_id="test_tenant", security="AAPL", quantity=100, updated=datetime.utcnow()))
        db.add(Position(account_id=1, tenant_id="test_tenant", security="GOOG", quantity=50, updated=datetime.utcnow()))
        db.add(Position(account_id=2, tenant_id="test_tenant", security="MSFT", quantity=200, updated=datetime.utcnow()))
        db.commit()
    finally:
        db.close()
