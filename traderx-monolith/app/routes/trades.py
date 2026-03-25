"""
Trade endpoints.
Ported from trade-service and position-service (trades query) Java/Spring implementations.

NOTE: The POST /trade/ endpoint calls trade_processor directly (in-process),
replacing the original pub/sub architecture. Some query endpoints use raw
SQLAlchemy queries inline instead of going through the service layer —
intentionally inconsistent (architectural smell).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.models.trade import Trade
from app.services import trade_processor
from app.utils.helpers import get_tenant_from_request

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
async def submit_trade(body: TradeOrderRequest, request: Request,
                       db: Session = Depends(get_db)):
    """
    Submit a new trade order.
    Processes the trade synchronously (in-process) instead of publishing
    to a message queue like the original microservice architecture.
    """
    tenant_id = get_tenant_from_request(request)

    logger.info("Trade order received: account=%d security=%s side=%s qty=%d",
                body.accountId, body.security, body.side, body.quantity)

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


# =============================================================================
# Trade Query Endpoints
# =============================================================================

@router.get("/trades/")
def list_all_trades(request: Request, db: Session = Depends(get_db)):
    """
    Get all trades for the current tenant.
    Uses raw SQLAlchemy query inline — bypasses service layer (intentional smell).
    """
    tenant_id = get_tenant_from_request(request)

    # Inline query — intentionally not using trade_processor.get_all_trades()
    trades = db.query(Trade).filter(
        Trade.tenant_id == tenant_id
    ).order_by(desc(Trade.created)).all()

    return [t.to_dict() for t in trades]


@router.get("/trades/{account_id}")
def list_trades_by_account(account_id: int, request: Request,
                           db: Session = Depends(get_db)):
    """
    Get all trades for a specific account.
    This one uses the service layer — intentionally inconsistent with list_all_trades.
    """
    tenant_id = get_tenant_from_request(request)
    trades = trade_processor.get_trades_for_account(db, account_id, tenant_id)
    return [t.to_dict() for t in trades]


# =============================================================================
# Trade Audit Trail Endpoint
# =============================================================================

@router.get("/trades/{trade_id}/audit")
def get_trade_audit_trail(trade_id: int, request: Request,
                          db: Session = Depends(get_db)):
    """
    Get the full audit trail for a specific trade.
    Returns chronological list of all state changes and events.
    """
    tenant_id = get_tenant_from_request(request)

    trade = trade_processor.get_trade_by_id(db, trade_id, tenant_id)
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")

    audit_entries = trade_processor.get_trade_audit_trail(db, trade_id, tenant_id)

    return {
        "tradeId": trade_id,
        "currentState": trade.state,
        "auditTrail": [entry.to_dict() for entry in audit_entries],
    }
