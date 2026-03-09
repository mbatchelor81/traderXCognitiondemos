"""Account CRUD service for users-service."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.models.account import Account, AccountUser

logger = logging.getLogger(__name__)


def get_account_by_id(db: Session, account_id: int, tenant_id: str) -> Optional[Account]:
    """Get a single account by ID and tenant."""
    return db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == tenant_id
    ).first()


def get_all_accounts(db: Session, tenant_id: str) -> List[Account]:
    """Get all accounts for a tenant."""
    return db.query(Account).filter(
        Account.tenant_id == tenant_id
    ).all()


def create_account(db: Session, display_name: str, tenant_id: str,
                   account_id: Optional[int] = None) -> Account:
    """Create a new account."""
    account = Account(
        display_name=display_name,
        tenant_id=tenant_id,
    )
    if account_id is not None:
        account.id = account_id

    db.add(account)
    db.commit()
    db.refresh(account)
    logger.info("Created account %d for tenant %s", account.id, tenant_id)
    return account


def upsert_account(db: Session, account_id: Optional[int], display_name: str,
                   tenant_id: str) -> Account:
    """Create or update an account."""
    if account_id is not None:
        existing = get_account_by_id(db, account_id, tenant_id)
        if existing is not None:
            existing.display_name = display_name
            db.commit()
            db.refresh(existing)
            return existing

    return create_account(db, display_name, tenant_id, account_id)


def get_account_user_by_id(db: Session, account_id: int, username: str,
                           tenant_id: str) -> Optional[AccountUser]:
    """Get a single account user by composite key."""
    return db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.username == username,
        AccountUser.tenant_id == tenant_id,
    ).first()


def get_all_account_users(db: Session, tenant_id: str) -> List[AccountUser]:
    """Get all account users for a tenant."""
    return db.query(AccountUser).filter(
        AccountUser.tenant_id == tenant_id
    ).all()


def create_account_user(db: Session, account_id: int, username: str,
                        tenant_id: str) -> AccountUser:
    """Create a new account user."""
    account_user = AccountUser(
        account_id=account_id,
        username=username,
        tenant_id=tenant_id,
    )
    db.add(account_user)
    db.commit()
    db.refresh(account_user)
    logger.info("Created account user %s for account %d tenant %s",
                username, account_id, tenant_id)
    return account_user


def upsert_account_user(db: Session, account_id: int, username: str,
                        tenant_id: str) -> AccountUser:
    """Create or update an account user."""
    existing = get_account_user_by_id(db, account_id, username, tenant_id)
    if existing is not None:
        return existing
    return create_account_user(db, account_id, username, tenant_id)
