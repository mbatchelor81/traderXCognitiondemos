"""
Account and AccountUser endpoints.

Paths and camelCase JSON match the monolith so the existing frontend keeps
working. Cross-domain data (positions, person validation) is fetched over HTTP
from peer services instead of from this service's database.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.clients import people_client, position_client
from app.clients.people_client import PeopleServiceUnavailable
from app.database import get_db
from app.logging_config import get_logger
from app.services import account_service
from app.utils import get_correlation_id_from_request, get_tenant_from_request

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class AccountCreate(BaseModel):
    id: Optional[int] = None
    displayName: str


class AccountUserCreate(BaseModel):
    accountId: int
    username: str


class AccountResponse(BaseModel):
    id: int
    tenant_id: str
    displayName: Optional[str] = None


class AccountDetailResponse(AccountResponse):
    positions: list[dict[str, Any]]


class AccountUserResponse(BaseModel):
    accountId: int
    tenant_id: str
    username: str


class AccountExistsResponse(BaseModel):
    exists: bool


# =============================================================================
# Account Endpoints
# =============================================================================

@router.get(
    "/account/",
    response_model=list[AccountResponse],
    summary="List all accounts for this tenant",
)
def list_accounts(request: Request, db: Session = Depends(get_db)):
    tenant_id = get_tenant_from_request(request)
    accounts = account_service.get_all_accounts(db, tenant_id)
    return [a.to_dict() for a in accounts]


@router.post(
    "/account/",
    response_model=AccountResponse,
    summary="Create an account",
)
def create_account(
    body: AccountCreate, request: Request, db: Session = Depends(get_db)
):
    tenant_id = get_tenant_from_request(request)
    account = account_service.upsert_account(
        db, body.id, body.displayName, tenant_id
    )
    return account.to_dict()


@router.put(
    "/account/",
    response_model=AccountResponse,
    summary="Update an account",
)
def update_account(
    body: AccountCreate, request: Request, db: Session = Depends(get_db)
):
    tenant_id = get_tenant_from_request(request)
    account = account_service.upsert_account(
        db, body.id, body.displayName, tenant_id
    )
    return account.to_dict()


@router.get(
    "/account/{account_id}/exists",
    response_model=AccountExistsResponse,
    summary="Check whether an account exists",
)
def account_exists(
    account_id: int, request: Request, db: Session = Depends(get_db)
):
    tenant_id = get_tenant_from_request(request)
    return {"exists": account_service.account_exists(db, account_id, tenant_id)}


@router.get(
    "/account/{account_id}",
    response_model=AccountDetailResponse,
    summary="Get one account with its positions",
    responses={404: {"description": "Account not found"}},
)
def get_account(
    account_id: int, request: Request, db: Session = Depends(get_db)
):
    """Positions come from position-service over HTTP; an unavailable peer
    yields an empty positions list rather than a failed request."""
    tenant_id = get_tenant_from_request(request)
    account = account_service.get_account_by_id(db, account_id, tenant_id)
    if account is None:
        raise HTTPException(
            status_code=404, detail=f"Account {account_id} not found"
        )

    positions = position_client.get_positions_for_account(
        account_id, get_correlation_id_from_request(request)
    )

    result = account.to_dict()
    result["positions"] = positions
    return result


# =============================================================================
# AccountUser Endpoints
# =============================================================================

@router.get(
    "/accountuser/",
    response_model=list[AccountUserResponse],
    summary="List account users, optionally filtered by account",
)
def list_account_users(
    request: Request,
    accountId: Optional[int] = Query(
        None, description="Restrict results to a single account"
    ),
    db: Session = Depends(get_db),
):
    tenant_id = get_tenant_from_request(request)
    users = account_service.get_all_account_users(db, tenant_id, accountId)
    return [u.to_dict() for u in users]


@router.post(
    "/accountuser/",
    response_model=AccountUserResponse,
    summary="Add a user to an account",
    responses={
        400: {"description": "Person is not valid in people-service"},
        503: {"description": "people-service is unreachable"},
    },
)
def create_account_user(
    body: AccountUserCreate, request: Request, db: Session = Depends(get_db)
):
    """The person is validated against people-service over HTTP before the
    membership row is written."""
    tenant_id = get_tenant_from_request(request)
    correlation_id = get_correlation_id_from_request(request)

    try:
        is_valid = people_client.validate_person(body.username, correlation_id)
    except PeopleServiceUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "people-service is unavailable; cannot validate "
                f"'{body.username}' right now."
            ),
        ) from exc

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"{body.username} not found in People service.",
        )

    user = account_service.upsert_account_user(
        db, body.accountId, body.username, tenant_id
    )
    return user.to_dict()


@router.put(
    "/accountuser/",
    response_model=AccountUserResponse,
    summary="Update an account user",
)
def update_account_user(
    body: AccountUserCreate, request: Request, db: Session = Depends(get_db)
):
    tenant_id = get_tenant_from_request(request)
    user = account_service.upsert_account_user(
        db, body.accountId, body.username, tenant_id
    )
    return user.to_dict()
