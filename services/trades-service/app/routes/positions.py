"""Position endpoints for trades-service."""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import get_db
from app.models.position import Position

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/positions/")
def list_all_positions(request: Request, db: Session = Depends(get_db)):
    """Get all positions for the current tenant."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    positions = db.query(Position).filter(
        Position.tenant_id == tenant_id
    ).all()
    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}")
def list_positions_by_account(account_id: int, request: Request,
                              db: Session = Depends(get_db)):
    """Get all positions for a specific account."""
    tenant_id = getattr(request.state, "tenant_id", TENANT_ID)
    positions = db.query(Position).filter(
        Position.account_id == account_id,
        Position.tenant_id == tenant_id,
    ).all()
    return [p.to_dict() for p in positions]
