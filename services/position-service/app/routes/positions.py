"""
Position endpoints.

Paths and camelCase JSON are kept identical to traderx-monolith/app/routes/positions.py.
Handlers stay thin: every read and write goes through app.services.position_service.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.logging_config import get_logger
from app.services import position_service
from app.utils.helpers import get_tenant_from_request

logger = get_logger(__name__)

router = APIRouter()


class PositionResponse(BaseModel):
    """A position, in the monolith's camelCase shape."""

    accountId: int
    tenant_id: str
    security: str
    quantity: int
    updated: Optional[str] = None


class ApplyPositionRequest(BaseModel):
    """A position delta produced by a trade."""

    accountId: int
    security: str = Field(min_length=1, max_length=50)
    quantityDelta: int


class RecalculateTrade(BaseModel):
    """One trade supplied by the caller for recalculation."""

    security: str = Field(min_length=1, max_length=50)
    side: str
    quantity: int


class RecalculateRequest(BaseModel):
    """Recalculate an account's positions from the caller's trades."""

    accountId: int
    trades: List[RecalculateTrade] = Field(default_factory=list)


@router.get("/positions/", response_model=List[PositionResponse],
            summary="List all positions for this tenant")
def list_all_positions(request: Request, db: Session = Depends(get_db)):
    """Get all positions for the tenant this instance serves."""
    tenant_id = get_tenant_from_request(request)
    positions = position_service.get_all_positions(db, tenant_id)
    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}", response_model=List[PositionResponse],
            summary="List positions for one account")
def list_positions_by_account(account_id: int, request: Request,
                              db: Session = Depends(get_db)):
    """Get all positions for a specific account. An unknown account yields []."""
    tenant_id = get_tenant_from_request(request)
    positions = position_service.get_positions_for_account(db, account_id, tenant_id)
    return [p.to_dict() for p in positions]


@router.post("/positions/apply", response_model=PositionResponse,
             summary="Apply a quantity delta to a position")
def apply_position(payload: ApplyPositionRequest, request: Request,
                   db: Session = Depends(get_db)):
    """
    Apply a quantity delta to an account/security position, creating it when
    it does not exist. This is the write API trading-service depends on.
    """
    tenant_id = get_tenant_from_request(request)
    position = position_service.apply_position_delta(
        db, payload.accountId, payload.security, payload.quantityDelta, tenant_id
    )
    return position.to_dict()


@router.post("/positions/recalculate", response_model=List[PositionResponse],
             summary="Recalculate an account's positions from supplied trades")
def recalculate_positions(payload: RecalculateRequest, request: Request,
                          db: Session = Depends(get_db)):
    """
    Recompute the account's positions from the trades supplied by the caller and
    return the recomputed positions. position-service owns no trades table, so
    the caller decides which trades count.
    """
    tenant_id = get_tenant_from_request(request)
    positions = position_service.recalculate_positions(
        db, payload.accountId, [t.model_dump() for t in payload.trades], tenant_id
    )
    return [p.to_dict() for p in positions]
