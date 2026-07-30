"""
Trade endpoints. Handlers stay thin — all work happens in trade_processor.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.clients import PeerServiceError
from app.database import get_db
from app.logging_config import get_logger
from app.services import trade_processor
from app.utils.helpers import get_tenant_from_request

logger = get_logger(__name__)

router = APIRouter()


class TradeOrderRequest(BaseModel):
    accountId: int
    security: str
    side: str
    quantity: int


class TradeResponse(BaseModel):
    id: int
    tenant_id: str
    accountId: int
    security: str
    side: str
    quantity: int
    state: str
    created: Optional[str] = None
    updated: Optional[str] = None


class TradeSubmissionResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    trade: Optional[TradeResponse] = None
    position: Optional[Dict[str, Any]] = None


@router.post(
    "/trade/",
    summary="Submit a trade order",
    response_model=TradeSubmissionResponse,
    responses={
        400: {"description": "Trade rejected by validation"},
        502: {"description": "A peer service required to process the trade failed"},
    },
    tags=["Trades"],
)
async def submit_trade(
    body: TradeOrderRequest, request: Request, db: Session = Depends(get_db)
) -> TradeSubmissionResponse:
    """
    Submit a new trade order. The account and security are validated against
    account-service and reference-data-service, and the resulting position delta
    is applied by position-service.
    """
    tenant_id = get_tenant_from_request(request)

    logger.info(
        "trade_order_received",
        extra={
            "account_id": body.accountId,
            "security": body.security,
            "side": body.side,
            "quantity": body.quantity,
            "tenant_id": tenant_id,
        },
    )

    try:
        result = await trade_processor.process_trade(
            db=db,
            account_id=body.accountId,
            security=body.security,
            side=body.side,
            quantity=body.quantity,
            tenant_id=tenant_id,
        )
    except PeerServiceError as exc:
        logger.error(
            "trade_rejected_peer_unavailable",
            extra={
                "account_id": body.accountId,
                "peer_service": exc.service,
                "reason": exc.reason,
            },
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return TradeSubmissionResponse(**result)


@router.get(
    "/trades/",
    summary="List all trades for this tenant",
    response_model=List[TradeResponse],
    tags=["Trades"],
)
def list_all_trades(
    request: Request, db: Session = Depends(get_db)
) -> List[TradeResponse]:
    """Get every trade for the tenant this instance serves, newest first."""
    tenant_id = get_tenant_from_request(request)
    trades = trade_processor.get_all_trades(db, tenant_id)
    return [TradeResponse(**t.to_dict()) for t in trades]


@router.get(
    "/trades/{account_id}",
    summary="List trades for an account",
    response_model=List[TradeResponse],
    tags=["Trades"],
)
def list_trades_by_account(
    account_id: int, request: Request, db: Session = Depends(get_db)
) -> List[TradeResponse]:
    """Get all trades for a specific account, newest first."""
    tenant_id = get_tenant_from_request(request)
    trades = trade_processor.get_trades_for_account(db, account_id, tenant_id)
    return [TradeResponse(**t.to_dict()) for t in trades]
