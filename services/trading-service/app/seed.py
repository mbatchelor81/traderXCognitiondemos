"""
Trade seeding for the trading-service.

Seeds only the trades table, only for this deployment's TENANT_ID, and only when
the database is empty. Accounts, positions and people are seeded by the services
that own them.
"""

from datetime import timedelta
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import SessionLocal
from app.logging_config import get_logger
from app.models.trade import Trade
from app.utils.helpers import now_utc

logger = get_logger(__name__)

# (account_id, security, side, quantity, state, offset from base time)
TradeSeed = Tuple[int, str, str, int, str, timedelta]

ACME_CORP_TRADES: List[TradeSeed] = [
    (22214, "AAPL", "Buy", 100, "Settled", timedelta()),
    (22214, "MSFT", "Buy", 250, "Settled", timedelta(hours=1)),
    (22214, "GOOGL", "Buy", 50, "Settled", timedelta(hours=2)),
    (22214, "AAPL", "Sell", 30, "Settled", timedelta(days=1)),
    (22214, "TSLA", "Buy", 75, "Settled", timedelta(days=2)),
    (11413, "JPM", "Buy", 500, "Settled", timedelta(days=1)),
    (11413, "BAC", "Buy", 300, "Settled", timedelta(days=1, hours=2)),
    (11413, "GS", "Buy", 200, "Settled", timedelta(days=2)),
]

GLOBEX_INC_TRADES: List[TradeSeed] = [
    (42422, "BAC", "Buy", 1000, "Settled", timedelta()),
    (42422, "AMZN", "Buy", 150, "Settled", timedelta(hours=3)),
    (42422, "META", "Buy", 300, "Settled", timedelta(days=1)),
    (52355, "NVDA", "Buy", 200, "Settled", timedelta(days=1, hours=5)),
    (52355, "AMD", "Buy", 400, "Settled", timedelta(days=2)),
]

INITECH_TRADES: List[TradeSeed] = [
    (62654, "AAPL", "Buy", 500, "Settled", timedelta()),
    (62654, "MSFT", "Buy", 300, "Settled", timedelta(hours=2)),
    (62654, "AAPL", "Sell", 200, "Settled", timedelta(days=1)),
    (10031, "GOOGL", "Buy", 100, "Processing", timedelta(days=2)),
    (10031, "TSLA", "Buy", 150, "Settled", timedelta(days=3)),
    (44044, "NVDA", "Buy", 250, "Settled", timedelta(days=4)),
    (44044, "AMD", "Buy", 350, "Settled", timedelta(days=4, hours=3)),
    (44044, "INTC", "Buy", 600, "Settled", timedelta(days=5)),
]

# Demo datasets keyed by the tenant they were authored for. A tenant without its
# own dataset gets the acme_corp shape seeded under its own tenant id.
DEMO_DATASETS = {
    "acme_corp": (ACME_CORP_TRADES, timedelta(days=5)),
    "globex_inc": (GLOBEX_INC_TRADES, timedelta(days=3)),
    "initech": (INITECH_TRADES, timedelta(days=7)),
}


def is_database_empty(db: Session) -> bool:
    """Check whether this service's trades table has any rows."""
    return db.query(Trade).count() == 0


def seed_trades(db: Session, tenant_id: str = TENANT_ID) -> int:
    """Insert the demo trades for this tenant. Returns the number inserted."""
    seeds, age = DEMO_DATASETS.get(tenant_id, DEMO_DATASETS["acme_corp"])
    base_time = now_utc() - age

    for account_id, security, side, quantity, state, offset in seeds:
        created = base_time + offset
        db.add(
            Trade(
                tenant_id=tenant_id,
                account_id=account_id,
                security=security,
                side=side,
                quantity=quantity,
                state=state,
                created=created,
                updated=created + timedelta(seconds=5),
            )
        )
    db.flush()
    return len(seeds)


def seed_database() -> bool:
    """Seed this tenant's trades on first startup. Returns True when seeded."""
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            logger.info("seed_skipped", extra={"reason": "trades_already_present"})
            return False

        seeded = seed_trades(db, TENANT_ID)
        db.commit()
        logger.info("seed_complete", extra={"trade_count": seeded})
        return True
    except Exception as exc:  # noqa: BLE001 — surfaced after rollback
        logger.error("seed_failed", extra={"reason": str(exc)})
        db.rollback()
        raise
    finally:
        db.close()
