"""
Database seeding script for TraderX Monolith.
Populates the database with sample data distributed across 3 tenants.
Runs automatically on first startup if the database is empty.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import SessionLocal
from app.models.account import Account, AccountUser
from app.models.trade import Trade
from app.models.position import Position
from app.utils.helpers import now_utc

logger = logging.getLogger(__name__)


def is_database_empty(db: Session) -> bool:
    """Check if the database has any data."""
    account_count = db.query(Account).count()
    return account_count == 0


def seed_acme_corp(db: Session):
    """
    Seed data for acme_corp tenant.
    Accounts: Test Account 20 (id: 22214), Private Clients Fund TTXX (id: 11413)
    """
    tenant = "acme_corp"
    logger.info("Seeding data for tenant: %s", tenant)

    # Accounts
    acct1 = Account(id=22214, tenant_id=tenant, display_name="Test Account 20")
    acct2 = Account(id=11413, tenant_id=tenant,
                    display_name="Private Clients Fund TTXX")
    db.add(acct1)
    db.add(acct2)
    db.flush()

    # Account Users
    db.add(AccountUser(account_id=22214, tenant_id=tenant, username="jsmith"))
    db.add(AccountUser(account_id=22214, tenant_id=tenant, username="jdoe"))
    db.add(AccountUser(account_id=11413, tenant_id=tenant, username="mwilliams"))
    db.flush()

    # Trades for Test Account 20
    base_time = now_utc() - timedelta(days=5)
    trades_data = [
        ("AAPL", "Buy", 100, "Settled", base_time),
        ("MSFT", "Buy", 250, "Settled", base_time + timedelta(hours=1)),
        ("GOOGL", "Buy", 50, "Settled", base_time + timedelta(hours=2)),
        ("AAPL", "Sell", 30, "Settled", base_time + timedelta(days=1)),
        ("TSLA", "Buy", 75, "Settled", base_time + timedelta(days=2)),
    ]

    for security, side, qty, state, created in trades_data:
        trade = Trade(
            tenant_id=tenant,
            account_id=22214,
            security=security,
            side=side,
            quantity=qty,
            state=state,
            created=created,
            updated=created + timedelta(seconds=5),
        )
        db.add(trade)
    db.flush()

    # Trades for Private Clients Fund TTXX
    trades_data2 = [
        ("JPM", "Buy", 500, "Settled", base_time + timedelta(days=1)),
        ("BAC", "Buy", 300, "Settled", base_time + timedelta(days=1, hours=2)),
        ("GS", "Buy", 200, "Settled", base_time + timedelta(days=2)),
    ]

    for security, side, qty, state, created in trades_data2:
        trade = Trade(
            tenant_id=tenant,
            account_id=11413,
            security=security,
            side=side,
            quantity=qty,
            state=state,
            created=created,
            updated=created + timedelta(seconds=5),
        )
        db.add(trade)
    db.flush()

    # Positions for Test Account 20
    positions_data = [
        (22214, "AAPL", 70),
        (22214, "MSFT", 250),
        (22214, "GOOGL", 50),
        (22214, "TSLA", 75),
    ]

    for acct_id, security, qty in positions_data:
        pos = Position(
            account_id=acct_id,
            tenant_id=tenant,
            security=security,
            quantity=qty,
            updated=now_utc(),
        )
        db.add(pos)

    # Positions for Private Clients Fund TTXX
    positions_data2 = [
        (11413, "JPM", 500),
        (11413, "BAC", 300),
        (11413, "GS", 200),
    ]

    for acct_id, security, qty in positions_data2:
        pos = Position(
            account_id=acct_id,
            tenant_id=tenant,
            security=security,
            quantity=qty,
            updated=now_utc(),
        )
        db.add(pos)

    db.flush()
    logger.info("Seeded acme_corp: 2 accounts, 8 trades, 7 positions")


def seed_globex_inc(db: Session):
    """
    Seed data for globex_inc tenant.
    Accounts: Algo Execution Partners (id: 42422), Big Corporate Fund (id: 52355)
    """
    tenant = "globex_inc"
    logger.info("Seeding data for tenant: %s", tenant)

    # Accounts
    acct1 = Account(id=42422, tenant_id=tenant,
                    display_name="Algo Execution Partners")
    acct2 = Account(id=52355, tenant_id=tenant,
                    display_name="Big Corporate Fund")
    db.add(acct1)
    db.add(acct2)
    db.flush()

    # Account Users
    db.add(AccountUser(account_id=42422, tenant_id=tenant, username="dchen"))
    db.add(AccountUser(account_id=42422, tenant_id=tenant, username="etaylor"))
    db.add(AccountUser(account_id=52355, tenant_id=tenant, username="mgarcia"))
    db.flush()

    # Trades with existing BAC trade
    base_time = now_utc() - timedelta(days=3)
    trades_data = [
        (42422, "BAC", "Buy", 1000, "Settled", base_time),
        (42422, "AMZN", "Buy", 150, "Settled", base_time + timedelta(hours=3)),
        (42422, "META", "Buy", 300, "Settled",
         base_time + timedelta(days=1)),
        (52355, "NVDA", "Buy", 200, "Settled",
         base_time + timedelta(days=1, hours=5)),
        (52355, "AMD", "Buy", 400, "Settled", base_time + timedelta(days=2)),
    ]

    for acct_id, security, side, qty, state, created in trades_data:
        trade = Trade(
            tenant_id=tenant,
            account_id=acct_id,
            security=security,
            side=side,
            quantity=qty,
            state=state,
            created=created,
            updated=created + timedelta(seconds=5),
        )
        db.add(trade)
    db.flush()

    # Positions
    positions_data = [
        (42422, "BAC", 1000),
        (42422, "AMZN", 150),
        (42422, "META", 300),
        (52355, "NVDA", 200),
        (52355, "AMD", 400),
    ]

    for acct_id, security, qty in positions_data:
        pos = Position(
            account_id=acct_id,
            tenant_id=tenant,
            security=security,
            quantity=qty,
            updated=now_utc(),
        )
        db.add(pos)

    db.flush()
    logger.info("Seeded globex_inc: 2 accounts, 5 trades, 5 positions")


def seed_initech(db: Session):
    """
    Seed data for initech tenant.
    Accounts: Hedge Fund TXY1 (id: 62654), Internal Trading Book (id: 10031),
              Trading Account 1 (id: 44044)
    Multiple account users.
    """
    tenant = "initech"
    logger.info("Seeding data for tenant: %s", tenant)

    # Accounts
    acct1 = Account(id=62654, tenant_id=tenant,
                    display_name="Hedge Fund TXY1")
    acct2 = Account(id=10031, tenant_id=tenant,
                    display_name="Internal Trading Book")
    acct3 = Account(id=44044, tenant_id=tenant,
                    display_name="Trading Account 1")
    db.add(acct1)
    db.add(acct2)
    db.add(acct3)
    db.flush()

    # Account Users — multiple users per account
    users_data = [
        (62654, "tanderson"),
        (62654, "lmartinez"),
        (62654, "klee"),
        (10031, "pthompson"),
        (10031, "awilson"),
        (44044, "jmoore"),
        (44044, "sbrown"),
        (44044, "rjohnson"),
    ]

    for acct_id, username in users_data:
        db.add(AccountUser(account_id=acct_id, tenant_id=tenant,
                           username=username))
    db.flush()

    # Trades
    base_time = now_utc() - timedelta(days=7)
    trades_data = [
        (62654, "AAPL", "Buy", 500, "Settled", base_time),
        (62654, "MSFT", "Buy", 300, "Settled",
         base_time + timedelta(hours=2)),
        (62654, "AAPL", "Sell", 200, "Settled",
         base_time + timedelta(days=1)),
        (10031, "GOOGL", "Buy", 100, "Processing",
         base_time + timedelta(days=2)),
        (10031, "TSLA", "Buy", 150, "Settled",
         base_time + timedelta(days=3)),
        (44044, "NVDA", "Buy", 250, "Settled",
         base_time + timedelta(days=4)),
        (44044, "AMD", "Buy", 350, "Settled",
         base_time + timedelta(days=4, hours=3)),
        (44044, "INTC", "Buy", 600, "Settled",
         base_time + timedelta(days=5)),
    ]

    for acct_id, security, side, qty, state, created in trades_data:
        trade = Trade(
            tenant_id=tenant,
            account_id=acct_id,
            security=security,
            side=side,
            quantity=qty,
            state=state,
            created=created,
            updated=created + timedelta(seconds=5),
        )
        db.add(trade)
    db.flush()

    # Positions
    positions_data = [
        (62654, "AAPL", 300),
        (62654, "MSFT", 300),
        (10031, "GOOGL", 100),
        (10031, "TSLA", 150),
        (44044, "NVDA", 250),
        (44044, "AMD", 350),
        (44044, "INTC", 600),
    ]

    for acct_id, security, qty in positions_data:
        pos = Position(
            account_id=acct_id,
            tenant_id=tenant,
            security=security,
            quantity=qty,
            updated=now_utc(),
        )
        db.add(pos)

    db.flush()
    logger.info("Seeded initech: 3 accounts, 8 trades, 7 positions")


def seed_database():
    """
    Main seed function. Populates the database with sample data
    distributed across 3 tenants. Only runs if the database is empty.
    """
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            logger.info("Database already contains data, skipping seed")
            return False

        logger.info("=" * 60)
        logger.info("SEEDING DATABASE")
        logger.info("=" * 60)

        seed_acme_corp(db)
        seed_globex_inc(db)
        seed_initech(db)

        db.commit()

        logger.info("=" * 60)
        logger.info("DATABASE SEEDING COMPLETE")
        logger.info("  Tenants: acme_corp, globex_inc, initech")
        logger.info("  Total accounts: 7")
        logger.info("  Total trades: 21")
        logger.info("  Total positions: 19")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error("Error seeding database: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()
