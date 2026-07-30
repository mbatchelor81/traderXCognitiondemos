"""Shared fixtures for position-service tests."""
import os

# The tenant must be set before any application module is imported.
TEST_TENANT_ID = os.environ.setdefault("TENANT_ID", "test_tenant")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.position import Position  # noqa: E402,F401

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def seeded_positions(db_session):
    """Two positions for account 22214 in the test tenant."""
    from app.utils.helpers import now_utc

    db_session.add(Position(account_id=22214, tenant_id=TEST_TENANT_ID,
                            security="AAPL", quantity=70, updated=now_utc()))
    db_session.add(Position(account_id=11413, tenant_id=TEST_TENANT_ID,
                            security="JPM", quantity=500, updated=now_utc()))
    db_session.commit()
