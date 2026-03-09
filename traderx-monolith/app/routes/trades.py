"""
Trade endpoints.
Single-tenant version - no tenant_id handling.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trade import Trade
from app.services import trading_service
from app.utils.helpers import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request Models
# =============================================================================

class TradeOrderRequest(BaseModel):
    accountId: int
    security: str
    side: str
    quantity: int


# =============================================================================
# Trade Submission Endpoint
# =============================================================================

@router.post("/trade/")
async def submit_trade(body: TradeOrderRequest,
                       db: Session = Depends(get_db)):
    """Submit a new trade order. Processed synchronously in-process."""
    logger.info("Trade order received: account=%d security=%s side=%s qty=%d",
                body.accountId, body.security, body.side, body.quantity)

    result = await trading_service.process_trade(
        db=db,
        account_id=body.accountId,
        security=body.security,
        side=body.side,
        quantity=body.quantity,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# =============================================================================
# Trade Query Endpoints
# =============================================================================

@router.get("/trades/")
def list_all_trades(db: Session = Depends(get_db)):
    """Get all trades."""
    trades = db.query(Trade).order_by(desc(Trade.created)).all()
    return [t.to_dict() for t in trades]


@router.get("/trades/{account_id}")
def list_trades_by_account(account_id: int,
                           db: Session = Depends(get_db)):
    """Get all trades for a specific account."""
    trades = trading_service.get_trades_for_account(db, account_id)
    return [t.to_dict() for t in trades]
