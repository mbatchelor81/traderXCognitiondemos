"""
Database seed module for single-tenant deployment.
Seeds initial accounts, users, and sample trades.
"""

import logging

from app.database import SessionLocal, create_tables
from app.models.account import Account, AccountUser
from app.models.trade import Trade
from app.models.position import Position
from app.utils.helpers import now_utc

logger = logging.getLogger(__name__)


def seed_database():
    """Seed the database with initial data for a single tenant."""
    create_tables()
    db = SessionLocal()

    try:
        existing = db.query(Account).first()
        if existing is not None:
            logger.info("Database already seeded, skipping")
            return False

        logger.info("Seeding database with initial data...")

        # Create accounts
        accounts = [
            Account(id=1, display_name="Main Trading Account"),
            Account(id=2, display_name="Research Portfolio"),
            Account(id=3, display_name="Hedge Fund Alpha"),
        ]
        for account in accounts:
            db.add(account)
        db.flush()

        # Create account users
        users = [
            AccountUser(account_id=1, username="jsmith"),
            AccountUser(account_id=1, username="ajones"),
            AccountUser(account_id=2, username="jsmith"),
            AccountUser(account_id=3, username="mwilson"),
        ]
        for user in users:
            db.add(user)
        db.flush()

        # Create sample trades
        trades = [
            Trade(account_id=1, security="AAPL", side="Buy",
                  quantity=100, state="Settled",
                  created=now_utc(), updated=now_utc()),
            Trade(account_id=1, security="MSFT", side="Buy",
                  quantity=50, state="Settled",
                  created=now_utc(), updated=now_utc()),
            Trade(account_id=2, security="GOOGL", side="Buy",
                  quantity=25, state="Settled",
                  created=now_utc(), updated=now_utc()),
        ]
        for trade in trades:
            db.add(trade)
        db.flush()

        # Create matching positions for settled trades
        positions = [
            Position(account_id=1, security="AAPL", quantity=100, updated=now_utc()),
            Position(account_id=1, security="MSFT", quantity=50, updated=now_utc()),
            Position(account_id=2, security="GOOGL", quantity=25, updated=now_utc()),
        ]
        for position in positions:
            db.add(position)

        db.commit()
        logger.info("Database seeded successfully with %d accounts, %d users, %d trades, %d positions",
                     len(accounts), len(users), len(trades), len(positions))
        return True

    except Exception as e:
        db.rollback()
        logger.error("Error seeding database: %s", str(e))
        raise
    finally:
        db.close()
