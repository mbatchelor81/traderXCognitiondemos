"""Trade endpoints for Trades Service."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import get_db
from app.models.trade import Trade
from app.services import trade_processor

logger = logging.getLogger(__name__)

router = APIRouter()


class TradeOrderRequest(BaseModel):
    accountId: int
    security: str
    side: str
    quantity: int


@router.post("/trade/")
async def submit_trade(body: TradeOrderRequest, request: Request,
                       db: Session = Depends(get_db)):
    """Submit a new trade order."""
    tenant_id = request.state.tenant_id

    result = await trade_processor.process_trade(
        db=db,
        account_id=body.accountId,
        security=body.security,
        side=body.side,
        quantity=body.quantity,
        tenant_id=tenant_id,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/trades/")
def list_all_trades(request: Request, db: Session = Depends(get_db)):
    """Get all trades for the current tenant."""
    tenant_id = request.state.tenant_id
    trades = db.query(Trade).filter(
        Trade.tenant_id == tenant_id
    ).order_by(desc(Trade.created)).all()
    return [t.to_dict() for t in trades]


@router.get("/trades/{account_id}")
def list_trades_by_account(account_id: int, request: Request,
                           db: Session = Depends(get_db)):
    """Get all trades for a specific account."""
    tenant_id = request.state.tenant_id
    trades = trade_processor.get_trades_for_account(db, account_id, tenant_id)
    return [t.to_dict() for t in trades]
