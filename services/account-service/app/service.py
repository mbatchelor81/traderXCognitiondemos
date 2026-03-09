"""Account CRUD service layer."""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Account, AccountUser

logger = logging.getLogger(__name__)


def get_account_by_id(db: Session, account_id: int, tenant_id: str) -> Optional[Account]:
    return db.query(Account).filter(
        Account.id == account_id, Account.tenant_id == tenant_id
    ).first()


def get_all_accounts(db: Session, tenant_id: str) -> List[Account]:
    return db.query(Account).filter(Account.tenant_id == tenant_id).all()


def upsert_account(db: Session, account_id: Optional[int], display_name: str, tenant_id: str) -> Account:
    if account_id is not None:
        existing = get_account_by_id(db, account_id, tenant_id)
        if existing is not None:
            existing.display_name = display_name
            db.commit()
            db.refresh(existing)
            return existing
    account = Account(display_name=display_name, tenant_id=tenant_id)
    if account_id is not None:
        account.id = account_id
    db.add(account)
    db.commit()
    db.refresh(account)
    logger.info("Upserted account %d for tenant %s", account.id, tenant_id)
    return account


def get_all_account_users(db: Session, tenant_id: str) -> List[AccountUser]:
    return db.query(AccountUser).filter(AccountUser.tenant_id == tenant_id).all()


def upsert_account_user(db: Session, account_id: int, username: str, tenant_id: str) -> AccountUser:
    existing = db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.username == username,
        AccountUser.tenant_id == tenant_id,
    ).first()
    if existing is not None:
        return existing
    user = AccountUser(account_id=account_id, username=username, tenant_id=tenant_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created account user %s for account %d tenant %s", username, account_id, tenant_id)
    return user
