"""Position Service route handlers."""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import get_db
from app.models import Position

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_tenant(request: Request) -> str:
    return getattr(request.state, "tenant_id", TENANT_ID)


@router.get("/positions/")
def list_all_positions(request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    positions = db.query(Position).filter(Position.tenant_id == tenant_id).all()
    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}")
def list_positions_by_account(account_id: int, request: Request, db: Session = Depends(get_db)):
    tenant_id = _get_tenant(request)
    positions = db.query(Position).filter(
        Position.account_id == account_id, Position.tenant_id == tenant_id,
    ).all()
    return [p.to_dict() for p in positions]
