"""
Seed this tenant's account data on first startup.

Only accounts and account users are seeded — trades and positions belong to
other services. Ported from the account rows in the monolith's app/seed.py.
"""

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import SessionLocal
from app.logging_config import get_logger
from app.models.account import Account, AccountUser

logger = get_logger(__name__)

SEED_ACCOUNTS = [
    (22214, "Test Account 20"),
    (11413, "Private Clients Fund TTXX"),
]

SEED_ACCOUNT_USERS = [
    (22214, "jsmith"),
    (22214, "jdoe"),
    (11413, "mwilliams"),
]


def is_database_empty(db: Session) -> bool:
    """Check whether this tenant's account table has any rows."""
    return db.query(Account).count() == 0


def seed_database() -> bool:
    """Seed accounts and account users when the database is empty."""
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            logger.info("seed_skipped", extra={"reason": "database_not_empty"})
            return False

        for account_id, display_name in SEED_ACCOUNTS:
            db.add(
                Account(
                    id=account_id, tenant_id=TENANT_ID, display_name=display_name
                )
            )
        db.flush()

        for account_id, username in SEED_ACCOUNT_USERS:
            db.add(
                AccountUser(
                    account_id=account_id, tenant_id=TENANT_ID, username=username
                )
            )

        db.commit()
        logger.info(
            "seed_completed",
            extra={
                "accounts": len(SEED_ACCOUNTS),
                "account_users": len(SEED_ACCOUNT_USERS),
            },
        )
        return True
    except Exception as exc:
        db.rollback()
        logger.error("seed_failed", extra={"error": str(exc)})
        raise
    finally:
        db.close()
