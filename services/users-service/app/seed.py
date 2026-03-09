"""Database seeding for users-service."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import SessionLocal
from app.models.account import Account, AccountUser

logger = logging.getLogger(__name__)


def is_database_empty(db: Session) -> bool:
    """Check if the database has any data."""
    return db.query(Account).count() == 0


def seed_acme_corp(db: Session):
    """Seed data for acme_corp tenant."""
    tenant = "acme_corp"
    acct1 = Account(id=22214, tenant_id=tenant, display_name="Test Account 20")
    acct2 = Account(id=11413, tenant_id=tenant,
                    display_name="Private Clients Fund TTXX")
    db.add(acct1)
    db.add(acct2)
    db.flush()

    db.add(AccountUser(account_id=22214, tenant_id=tenant, username="jsmith"))
    db.add(AccountUser(account_id=22214, tenant_id=tenant, username="jdoe"))
    db.add(AccountUser(account_id=11413, tenant_id=tenant, username="mwilliams"))
    db.flush()
    logger.info("Seeded acme_corp: 2 accounts, 3 account users")


def seed_globex_inc(db: Session):
    """Seed data for globex_inc tenant."""
    tenant = "globex_inc"
    acct1 = Account(id=42422, tenant_id=tenant,
                    display_name="Algo Execution Partners")
    acct2 = Account(id=52355, tenant_id=tenant,
                    display_name="Big Corporate Fund")
    db.add(acct1)
    db.add(acct2)
    db.flush()

    db.add(AccountUser(account_id=42422, tenant_id=tenant, username="dchen"))
    db.add(AccountUser(account_id=42422, tenant_id=tenant, username="etaylor"))
    db.add(AccountUser(account_id=52355, tenant_id=tenant, username="mgarcia"))
    db.flush()
    logger.info("Seeded globex_inc: 2 accounts, 3 account users")


def seed_initech(db: Session):
    """Seed data for initech tenant."""
    tenant = "initech"
    acct1 = Account(id=62654, tenant_id=tenant, display_name="Hedge Fund TXY1")
    acct2 = Account(id=10031, tenant_id=tenant,
                    display_name="Internal Trading Book")
    acct3 = Account(id=44044, tenant_id=tenant,
                    display_name="Trading Account 1")
    db.add(acct1)
    db.add(acct2)
    db.add(acct3)
    db.flush()

    users_data = [
        (62654, "tanderson"), (62654, "lmartinez"), (62654, "klee"),
        (10031, "pthompson"), (10031, "awilson"),
        (44044, "jmoore"), (44044, "sbrown"), (44044, "rjohnson"),
    ]
    for acct_id, username in users_data:
        db.add(AccountUser(account_id=acct_id, tenant_id=tenant,
                           username=username))
    db.flush()
    logger.info("Seeded initech: 3 accounts, 8 account users")


_SEED_FUNCTIONS = {
    "acme_corp": seed_acme_corp,
    "globex_inc": seed_globex_inc,
    "initech": seed_initech,
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

        logger.info("Seeding users-service database for tenant: %s", TENANT_ID)
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
