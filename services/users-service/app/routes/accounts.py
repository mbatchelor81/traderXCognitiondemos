"""Account and AccountUser endpoints for users-service."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import get_db
from app.models.account import Account, AccountUser
from app.services import account_service
from app.services.people_service import validate_person

logger = logging.getLogger(__name__)

router = APIRouter()


class AccountCreate(BaseModel):
    id: Optional[int] = None
    displayName: str


class AccountUserCreate(BaseModel):
    accountId: int
    username: str


@router.get("/account/")
def list_accounts(request: Request, db: Session = Depends(get_db)):
    """List all accounts for the current tenant."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    accounts = account_service.get_all_accounts(db, tenant_id)
    return [a.to_dict() for a in accounts]


@router.post("/account/")
def create_account(body: AccountCreate, request: Request,
                   db: Session = Depends(get_db)):
    """Create a new account."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    account = account_service.upsert_account(
        db, body.id, body.displayName, tenant_id
    )
    return account.to_dict()


@router.put("/account/")
def update_account(body: AccountCreate, request: Request,
                   db: Session = Depends(get_db)):
    """Update an existing account."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    account = account_service.upsert_account(
        db, body.id, body.displayName, tenant_id
    )
    return account.to_dict()


@router.get("/account/{account_id}")
def get_account(account_id: int, request: Request,
                db: Session = Depends(get_db)):
    """Get account by ID."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    account = account_service.get_account_by_id(db, account_id, tenant_id)
    if account is None:
        raise HTTPException(status_code=404,
                            detail=f"Account {account_id} not found")
    return account.to_dict()


@router.get("/accountuser/")
def list_account_users(request: Request, db: Session = Depends(get_db)):
    """List all account users for the current tenant."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    users = account_service.get_all_account_users(db, tenant_id)
    return [u.to_dict() for u in users]


@router.post("/accountuser/")
def create_account_user(body: AccountUserCreate, request: Request,
                        db: Session = Depends(get_db)):
    """Create a new account user."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)

    if not validate_person(logon_id=body.username):
        raise HTTPException(
            status_code=404,
            detail=f"{body.username} not found in People service."
        )

    user = account_service.upsert_account_user(
        db, body.accountId, body.username, tenant_id
    )
    return user.to_dict()


@router.put("/accountuser/")
def update_account_user(body: AccountUserCreate, request: Request,
                        db: Session = Depends(get_db)):
    """Update an account user."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    user = account_service.upsert_account_user(
        db, body.accountId, body.username, tenant_id
    )
    return user.to_dict()
