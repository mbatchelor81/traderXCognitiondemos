"""
Account and AccountUser CRUD.

Ported from the monolith's app/services/account_service.py. The monolith's
`get_trade_count_for_account` / `can_delete_account` helpers are intentionally
dropped: trade counts belong to trading-service and account-service must not
depend on it.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models.account import Account, AccountUser
from app.utils import log_audit_event

logger = get_logger(__name__)


# =============================================================================
# Account CRUD
# =============================================================================

def get_account_by_id(
    db: Session, account_id: int, tenant_id: str
) -> Optional[Account]:
    """Get a single account by ID and tenant."""
    return db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == tenant_id,
    ).first()


def get_all_accounts(db: Session, tenant_id: str) -> List[Account]:
    """Get all accounts for a tenant."""
    return db.query(Account).filter(Account.tenant_id == tenant_id).all()


def account_exists(db: Session, account_id: int, tenant_id: str) -> bool:
    """Cheap existence check used by peer services."""
    return db.query(Account.id).filter(
        Account.id == account_id,
        Account.tenant_id == tenant_id,
    ).first() is not None


def create_account(
    db: Session,
    display_name: str,
    tenant_id: str,
    account_id: Optional[int] = None,
) -> Account:
    """Create a new account."""
    account = Account(display_name=display_name, tenant_id=tenant_id)
    if account_id is not None:
        account.id = account_id

    db.add(account)
    db.commit()
    db.refresh(account)
    log_audit_event(
        "ACCOUNT_CREATED",
        tenant_id,
        account_id=account.id,
        display_name=display_name,
    )
    logger.info(
        "account_created",
        extra={"account_id": account.id, "action": "created"},
    )
    return account


def update_account(
    db: Session, account_id: int, display_name: str, tenant_id: str
) -> Optional[Account]:
    """Update an existing account, or None when it does not exist."""
    account = get_account_by_id(db, account_id, tenant_id)
    if account is None:
        return None

    account.display_name = display_name
    db.commit()
    db.refresh(account)
    log_audit_event(
        "ACCOUNT_UPDATED",
        tenant_id,
        account_id=account.id,
        display_name=display_name,
    )
    logger.info(
        "account_updated",
        extra={"account_id": account.id, "action": "updated"},
    )
    return account


def upsert_account(
    db: Session, account_id: Optional[int], display_name: str, tenant_id: str
) -> Account:
    """Create or update an account (mirrors the monolith's upsertAccount)."""
    if account_id is not None:
        existing = get_account_by_id(db, account_id, tenant_id)
        if existing is not None:
            existing.display_name = display_name
            db.commit()
            db.refresh(existing)
            return existing

    return create_account(db, display_name, tenant_id, account_id)


# =============================================================================
# AccountUser CRUD
# =============================================================================

def get_account_user_by_id(
    db: Session, account_id: int, username: str, tenant_id: str
) -> Optional[AccountUser]:
    """Get a single account user by composite key."""
    return db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.username == username,
        AccountUser.tenant_id == tenant_id,
    ).first()


def get_all_account_users(
    db: Session, tenant_id: str, account_id: Optional[int] = None
) -> List[AccountUser]:
    """Get account users for a tenant, optionally filtered to one account."""
    query = db.query(AccountUser).filter(AccountUser.tenant_id == tenant_id)
    if account_id is not None:
        query = query.filter(AccountUser.account_id == account_id)
    return query.all()


def create_account_user(
    db: Session, account_id: int, username: str, tenant_id: str
) -> AccountUser:
    """Create a new account user."""
    account_user = AccountUser(
        account_id=account_id,
        username=username,
        tenant_id=tenant_id,
    )
    db.add(account_user)
    db.commit()
    db.refresh(account_user)
    log_audit_event(
        "ACCOUNT_USER_CREATED",
        tenant_id,
        account_id=account_id,
        username=username,
    )
    logger.info(
        "account_user_created",
        extra={"account_id": account_id, "username": username, "action": "created"},
    )
    return account_user


def upsert_account_user(
    db: Session, account_id: int, username: str, tenant_id: str
) -> AccountUser:
    """Create or update an account user."""
    existing = get_account_user_by_id(db, account_id, username, tenant_id)
    if existing is not None:
        return existing
    return create_account_user(db, account_id, username, tenant_id)
