"""
Trade analytics endpoints.
"""

from typing import Dict

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics_service
from app.utils.helpers import get_tenant_from_request

router = APIRouter()


class RecentActivity(BaseModel):
    last7Days: int
    last30Days: int


class TradeStatisticsResponse(BaseModel):
    totalTrades: int
    averageQuantity: float
    buyCount: int
    sellCount: int
    buySellRatio: float
    tradesByState: Dict[str, int]
    tradesBySecurity: Dict[str, int]
    recentActivity: RecentActivity


class AccountTradeStatisticsResponse(BaseModel):
    accountId: int
    totalTrades: int
    averageQuantity: float
    buyCount: int
    sellCount: int
    tradesByState: Dict[str, int]
    tradesBySecurity: Dict[str, int]


@router.get(
    "/analytics/trades",
    summary="Trade statistics for this tenant",
    response_model=TradeStatisticsResponse,
    tags=["Analytics"],
)
def get_trade_analytics(
    request: Request, db: Session = Depends(get_db)
) -> TradeStatisticsResponse:
    """
    Aggregated trade metrics: totals, average quantity, buy/sell split and
    ratio, counts by state and security, and activity over the last 7/30 days.
    """
    tenant_id = get_tenant_from_request(request)
    return TradeStatisticsResponse(
        **analytics_service.get_trade_statistics(db, tenant_id)
    )


@router.get(
    "/analytics/trades/{account_id}",
    summary="Trade statistics for a single account",
    response_model=AccountTradeStatisticsResponse,
    tags=["Analytics"],
)
def get_account_trade_analytics(
    account_id: int, request: Request, db: Session = Depends(get_db)
) -> AccountTradeStatisticsResponse:
    """Account-scoped trade metrics: totals, average quantity, buy/sell counts."""
    tenant_id = get_tenant_from_request(request)
    return AccountTradeStatisticsResponse(
        **analytics_service.get_account_trade_statistics(db, account_id, tenant_id)
    )
