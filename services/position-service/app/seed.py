"""
Seed the position database for this instance's tenant.

Ported from the position rows of traderx-monolith/app/seed.py — accounts and
trades belong to other services and are not seeded here. Runs on first startup
only, when the positions table is empty.
"""

from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import SessionLocal
from app.logging_config import get_logger
from app.models.position import Position
from app.utils.helpers import now_utc

logger = get_logger(__name__)

# (account_id, security, quantity) — the monolith's position seed rows.
ACME_CORP_POSITIONS: List[Tuple[int, str, int]] = [
    (22214, "AAPL", 70),
    (22214, "MSFT", 250),
    (22214, "GOOGL", 50),
    (22214, "TSLA", 75),
    (11413, "JPM", 500),
    (11413, "BAC", 300),
    (11413, "GS", 200),
]

GLOBEX_INC_POSITIONS: List[Tuple[int, str, int]] = [
    (42422, "BAC", 1000),
    (42422, "AMZN", 150),
    (42422, "META", 300),
    (52355, "NVDA", 200),
    (52355, "AMD", 400),
]

INITECH_POSITIONS: List[Tuple[int, str, int]] = [
    (62654, "AAPL", 300),
    (62654, "MSFT", 300),
    (10031, "GOOGL", 100),
    (10031, "TSLA", 150),
    (44044, "NVDA", 250),
    (44044, "AMD", 350),
    (44044, "INTC", 600),
]

# A tenant without its own dataset gets the acme_corp shape under its own id.
DEMO_DATASETS: Dict[str, List[Tuple[int, str, int]]] = {
    "acme_corp": ACME_CORP_POSITIONS,
    "globex_inc": GLOBEX_INC_POSITIONS,
    "initech": INITECH_POSITIONS,
}


def is_database_empty(db: Session) -> bool:
    """Check whether this tenant has any positions yet."""
    return db.query(Position).filter(Position.tenant_id == TENANT_ID).count() == 0


def seed_positions(db: Session, tenant_id: str) -> int:
    """Insert the demo positions for a tenant. Returns the number of rows added."""
    rows = DEMO_DATASETS.get(tenant_id, ACME_CORP_POSITIONS)
    for account_id, security, quantity in rows:
        db.add(Position(
            account_id=account_id,
            tenant_id=tenant_id,
            security=security,
            quantity=quantity,
            updated=now_utc(),
        ))
    db.flush()
    return len(rows)


def seed_database() -> bool:
    """Seed this instance's tenant positions if the database is empty."""
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            logger.info("seed_skipped", extra={"reason": "database_not_empty"})
            return False

        count = seed_positions(db, TENANT_ID)
        db.commit()
        logger.info("seed_complete", extra={"positions": count})
        return True

    except Exception as exc:
        logger.error("seed_failed", extra={"error": str(exc)})
        db.rollback()
        raise
    finally:
        db.close()
