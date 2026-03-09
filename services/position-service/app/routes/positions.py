"""Position endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import get_db
from app.models.position import Position

logger = logging.getLogger(__name__)

router = APIRouter()


class PositionUpdate(BaseModel):
    accountId: int
    security: str
    side: str
    quantity: int
    tenant_id: str


@router.get("/positions/")
def list_all_positions(db: Session = Depends(get_db)):
    positions = db.query(Position).filter(Position.tenant_id == TENANT_ID).all()
    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}")
def list_positions_by_account(account_id: int, db: Session = Depends(get_db)):
    positions = db.query(Position).filter(
        Position.account_id == account_id,
        Position.tenant_id == TENANT_ID,
    ).all()
    return [p.to_dict() for p in positions]


@router.post("/positions/update")
def update_position(body: PositionUpdate, db: Session = Depends(get_db)):
    """Update position after a trade settles. Called by Trading Service."""
    quantity_delta = body.quantity if body.side == "Buy" else -body.quantity

    position = db.query(Position).filter(
        Position.account_id == body.accountId,
        Position.security == body.security,
        Position.tenant_id == TENANT_ID,
    ).first()

    if position is None:
        position = Position(
            account_id=body.accountId,
            security=body.security,
            tenant_id=TENANT_ID,
            quantity=0,
            updated=datetime.utcnow(),
        )
        db.add(position)

    position.quantity = position.quantity + quantity_delta
    position.updated = datetime.utcnow()
    db.commit()
    db.refresh(position)

    logger.info("Position updated: account=%d security=%s qty=%d",
                body.accountId, body.security, position.quantity,
                extra={"tenant_id": TENANT_ID, "service": "position-service"})
    return position.to_dict()
