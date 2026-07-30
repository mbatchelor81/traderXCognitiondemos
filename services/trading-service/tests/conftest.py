"""
Shared pytest fixtures for the trading-service.

TENANT_ID must be set before any application module is imported, because
app.config resolves it at import time and raises without it.
"""

import os

os.environ.setdefault("TENANT_ID", "test_tenant")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config import TENANT_ID  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.trade import Trade  # noqa: E402

TEST_ACCOUNT_ID = 22214


@pytest.fixture
def db_session():
    """In-memory SQLite session, recreated for every test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    """TestClient wired to the in-memory database."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_trades(db_session):
    """A small, deterministic set of trades for the test tenant."""
    from datetime import datetime, timedelta

    base = datetime.utcnow() - timedelta(days=1)
    trades = [
        Trade(tenant_id=TENANT_ID, account_id=TEST_ACCOUNT_ID, security="AAPL",
              side="Buy", quantity=100, state="Settled", created=base, updated=base),
        Trade(tenant_id=TENANT_ID, account_id=TEST_ACCOUNT_ID, security="AAPL",
              side="Sell", quantity=40, state="Settled",
              created=base + timedelta(hours=1), updated=base + timedelta(hours=1)),
        Trade(tenant_id=TENANT_ID, account_id=11413, security="MSFT",
              side="Buy", quantity=250, state="Processing",
              created=base + timedelta(hours=2), updated=base + timedelta(hours=2)),
    ]
    for trade in trades:
        db_session.add(trade)
    db_session.commit()
    return trades
