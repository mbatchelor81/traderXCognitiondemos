"""Trade endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import TENANT_ID
from app.database import get_db
from app.services import trade_processor

logger = logging.getLogger(__name__)

router = APIRouter()


class TradeOrderRequest(BaseModel):
    accountId: int
    security: str
    side: str
    quantity: int


@router.post("/trade/")
async def submit_trade(body: TradeOrderRequest, db: Session = Depends(get_db)):
    result = await trade_processor.process_trade(
        db=db, account_id=body.accountId, security=body.security,
        side=body.side, quantity=body.quantity, tenant_id=TENANT_ID,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/trades/")
def list_all_trades(db: Session = Depends(get_db)):
    trades = trade_processor.get_all_trades(db, TENANT_ID)
    return [t.to_dict() for t in trades]


@router.get("/trades/{account_id}")
def list_trades_by_account(account_id: int, db: Session = Depends(get_db)):
    trades = trade_processor.get_trades_for_account(db, account_id, TENANT_ID)
    return [t.to_dict() for t in trades]
