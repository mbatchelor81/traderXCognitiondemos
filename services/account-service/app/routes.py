"""Account Service route handlers."""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import TENANT_ID, PEOPLE_SERVICE_URL
from app.database import get_db
from app import service as account_service

logger = logging.getLogger(__name__)
router = APIRouter()


class AccountCreate(BaseModel):
    id: Optional[int] = None
    displayName: str


class AccountUserCreate(BaseModel):
    accountId: int
    username: str


def _get_tenant(request: Request) -> str:
    return getattr(request.state, "tenant_id", TENANT_ID)


@router.get("/account/")
def list_accounts(request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    accounts = account_service.get_all_accounts(db, tenant_id)
    return [a.to_dict() for a in accounts]


@router.post("/account/")
def create_account(body: AccountCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    account = account_service.upsert_account(db, body.id, body.displayName, tenant_id)
    return account.to_dict()


@router.put("/account/")
def update_account(body: AccountCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    account = account_service.upsert_account(db, body.id, body.displayName, tenant_id)
    return account.to_dict()


@router.get("/account/{account_id}")
def get_account(account_id: int, request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    account = account_service.get_account_by_id(db, account_id, tenant_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return account.to_dict()


@router.get("/accountuser/")
def list_account_users(request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    users = account_service.get_all_account_users(db, tenant_id)
    return [u.to_dict() for u in users]


@router.post("/accountuser/")
def create_account_user(body: AccountUserCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    # Validate person via People Service HTTP call
    try:
        resp = httpx.get(f"{PEOPLE_SERVICE_URL}/people/ValidatePerson", params={"LogonId": body.username}, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            if not data.get("IsValid", False):
                raise HTTPException(status_code=404, detail=f"{body.username} not found in People service.")
        else:
            logger.warning("People service returned %d, proceeding without validation", resp.status_code)
    except httpx.RequestError as e:
        logger.warning("People service unavailable (%s), proceeding without validation", str(e))

    user = account_service.upsert_account_user(db, body.accountId, body.username, tenant_id)
    return user.to_dict()


@router.put("/accountuser/")
def update_account_user(body: AccountUserCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    user = account_service.upsert_account_user(db, body.accountId, body.username, tenant_id)
    return user.to_dict()
