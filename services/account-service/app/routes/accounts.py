"""Account and AccountUser endpoints."""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import TENANT_ID, PEOPLE_SERVICE_URL
from app.database import get_db
from app.services import account_service


def _trace_headers() -> dict:
    """Build outbound headers with traceparent propagation."""
    headers: dict = {}
    try:
        from opentelemetry.propagate import inject
        inject(headers)
    except ImportError:
        pass
    return headers

logger = logging.getLogger(__name__)

router = APIRouter()


class AccountCreate(BaseModel):
    id: Optional[int] = None
    displayName: str


class AccountUserCreate(BaseModel):
    accountId: int
    username: str


@router.get("/account/")
def list_accounts(db: Session = Depends(get_db)):
    accounts = account_service.get_all_accounts(db, TENANT_ID)
    return [a.to_dict() for a in accounts]


@router.post("/account/")
def create_account(body: AccountCreate, db: Session = Depends(get_db)):
    account = account_service.upsert_account(db, body.id, body.displayName, TENANT_ID)
    return account.to_dict()


@router.put("/account/")
def update_account(body: AccountCreate, db: Session = Depends(get_db)):
    account = account_service.upsert_account(db, body.id, body.displayName, TENANT_ID)
    return account.to_dict()


@router.get("/account/{account_id}")
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = account_service.get_account_by_id(db, account_id, TENANT_ID)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return account.to_dict()


@router.get("/accountuser/")
def list_account_users(db: Session = Depends(get_db)):
    users = account_service.get_all_account_users(db, TENANT_ID)
    return [u.to_dict() for u in users]


@router.post("/accountuser/")
def create_account_user(body: AccountUserCreate, db: Session = Depends(get_db)):
    """Create account user. Validates person via People Service HTTP call."""
    try:
        resp = httpx.get(
            f"{PEOPLE_SERVICE_URL}/people/ValidatePerson",
            params={"LogonId": body.username},
            timeout=5.0,
            headers=_trace_headers(),
        )
        if resp.status_code == 200:
            data = resp.json()
            if not data.get("IsValid", False):
                raise HTTPException(status_code=404,
                                    detail=f"{body.username} not found in People service.")
        else:
            logger.warning("People service returned %d, allowing user creation", resp.status_code)
    except httpx.RequestError as e:
        logger.warning("People service unavailable (%s), allowing user creation", str(e))

    user = account_service.upsert_account_user(db, body.accountId, body.username, TENANT_ID)
    return user.to_dict()


@router.put("/accountuser/")
def update_account_user(body: AccountUserCreate, db: Session = Depends(get_db)):
    user = account_service.upsert_account_user(db, body.accountId, body.username, TENANT_ID)
    return user.to_dict()
