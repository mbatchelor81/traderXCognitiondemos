"""
Position endpoints.
Single-tenant version - no tenant_id handling.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.position import Position

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/positions/")
def list_all_positions(db: Session = Depends(get_db)):
    """Get all positions."""
    positions = db.query(Position).all()
    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}")
def list_positions_by_account(account_id: int,
                              db: Session = Depends(get_db)):
    """Get all positions for a specific account."""
    positions = db.query(Position).filter(
        Position.account_id == account_id,
    ).all()
    return [p.to_dict() for p in positions]
