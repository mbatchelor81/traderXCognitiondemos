"""Database seeding for trades-service."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import SessionLocal
from app.models.trade import Trade
from app.models.position import Position

logger = logging.getLogger(__name__)


def is_database_empty(db: Session) -> bool:
    """Check if the database has any trade data."""
    return db.query(Trade).count() == 0


def _update_position(db: Session, account_id: int, security: str,
                     quantity: int, tenant_id: str):
    """Helper to upsert a position."""
    pos = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()
    if pos:
        pos.quantity = pos.quantity + quantity
        pos.updated = datetime.utcnow()
    else:
        pos = Position(
            account_id=account_id,
            security=security,
            tenant_id=tenant_id,
            quantity=quantity,
            updated=datetime.utcnow(),
        )
        db.add(pos)


def seed_acme_corp(db: Session):
    """Seed trades and positions for acme_corp."""
    tenant = "acme_corp"
    trades = [
        Trade(tenant_id=tenant, account_id=22214, security="AAPL",
              side="Buy", quantity=100, state="Settled",
              created=datetime.utcnow(), updated=datetime.utcnow()),
        Trade(tenant_id=tenant, account_id=22214, security="MSFT",
              side="Buy", quantity=50, state="Settled",
              created=datetime.utcnow(), updated=datetime.utcnow()),
        Trade(tenant_id=tenant, account_id=11413, security="GOOGL",
              side="Buy", quantity=75, state="Settled",
              created=datetime.utcnow(), updated=datetime.utcnow()),
    ]
    db.add_all(trades)
    db.flush()

    _update_position(db, 22214, "AAPL", 100, tenant)
    _update_position(db, 22214, "MSFT", 50, tenant)
    _update_position(db, 11413, "GOOGL", 75, tenant)
    db.flush()
    logger.info("Seeded acme_corp: 3 trades, 3 positions")


def seed_globex_inc(db: Session):
    """Seed trades and positions for globex_inc."""
    tenant = "globex_inc"
    trades = [
        Trade(tenant_id=tenant, account_id=42422, security="AMZN",
              side="Buy", quantity=200, state="Settled",
              created=datetime.utcnow(), updated=datetime.utcnow()),
        Trade(tenant_id=tenant, account_id=52355, security="NVDA",
              side="Buy", quantity=150, state="Settled",
              created=datetime.utcnow(), updated=datetime.utcnow()),
    ]
    db.add_all(trades)
    db.flush()

    _update_position(db, 42422, "AMZN", 200, tenant)
    _update_position(db, 52355, "NVDA", 150, tenant)
    db.flush()
    logger.info("Seeded globex_inc: 2 trades, 2 positions")


_SEED_FUNCTIONS = {
    "acme_corp": seed_acme_corp,
    "globex_inc": seed_globex_inc,
}


def seed_database():
    """Seed the database for the current TENANT_ID."""
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            logger.info("Database already contains data, skipping seed")
            return False

        seed_fn = _SEED_FUNCTIONS.get(TENANT_ID)
        if seed_fn is None:
            logger.info("No seed data for tenant '%s', skipping", TENANT_ID)
            return False

        logger.info("Seeding trades-service database for tenant: %s", TENANT_ID)
        seed_fn(db)
        db.commit()
        logger.info("Seed complete for tenant: %s", TENANT_ID)
        return True

    except Exception as e:
        logger.error("Error seeding database: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()
