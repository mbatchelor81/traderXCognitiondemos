"""
Trade analytics for the trading-service.

Ported unchanged from the monolith's analytics_service — every metric here is
derived from the trades table this service owns, so no cross-service call is
needed.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models.trade import Trade

logger = get_logger(__name__)


def get_trade_statistics(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Comprehensive trade statistics for the tenant: totals, average quantity,
    buy/sell split, counts by state and security, and recent activity.
    """
    base_query = db.query(Trade).filter(Trade.tenant_id == tenant_id)
    total_trades = base_query.count()

    if total_trades == 0:
        return {
            "totalTrades": 0,
            "averageQuantity": 0,
            "buyCount": 0,
            "sellCount": 0,
            "buySellRatio": 0,
            "tradesByState": {},
            "tradesBySecurity": {},
            "recentActivity": {"last7Days": 0, "last30Days": 0},
        }

    avg_quantity = db.query(func.avg(Trade.quantity)).filter(
        Trade.tenant_id == tenant_id
    ).scalar() or 0

    buy_count = base_query.filter(Trade.side == "Buy").count()
    sell_count = base_query.filter(Trade.side == "Sell").count()
    buy_sell_ratio = buy_count / sell_count if sell_count > 0 else buy_count

    trades_by_state = dict(
        db.query(Trade.state, func.count(Trade.id))
        .filter(Trade.tenant_id == tenant_id)
        .group_by(Trade.state)
        .all()
    )

    trades_by_security = dict(
        db.query(Trade.security, func.count(Trade.id))
        .filter(Trade.tenant_id == tenant_id)
        .group_by(Trade.security)
        .order_by(func.count(Trade.id).desc())
        .limit(10)
        .all()
    )

    now = datetime.utcnow()
    last_7_days = base_query.filter(Trade.created >= now - timedelta(days=7)).count()
    last_30_days = base_query.filter(Trade.created >= now - timedelta(days=30)).count()

    statistics = {
        "totalTrades": total_trades,
        "averageQuantity": round(float(avg_quantity), 2),
        "buyCount": buy_count,
        "sellCount": sell_count,
        "buySellRatio": round(float(buy_sell_ratio), 2),
        "tradesByState": trades_by_state,
        "tradesBySecurity": trades_by_security,
        "recentActivity": {"last7Days": last_7_days, "last30Days": last_30_days},
    }

    logger.info(
        "trade_statistics_generated",
        extra={"tenant_id": tenant_id, "total_trades": total_trades},
    )
    return statistics


def get_account_trade_statistics(
    db: Session, account_id: int, tenant_id: str
) -> Dict[str, Any]:
    """Trade statistics for a single account within the tenant."""
    base_query = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
        Trade.account_id == account_id,
    )
    total_trades = base_query.count()

    if total_trades == 0:
        return {
            "accountId": account_id,
            "totalTrades": 0,
            "averageQuantity": 0,
            "buyCount": 0,
            "sellCount": 0,
            "tradesByState": {},
            "tradesBySecurity": {},
        }

    avg_quantity = db.query(func.avg(Trade.quantity)).filter(
        Trade.tenant_id == tenant_id,
        Trade.account_id == account_id,
    ).scalar() or 0

    buy_count = base_query.filter(Trade.side == "Buy").count()
    sell_count = base_query.filter(Trade.side == "Sell").count()

    trades_by_state = dict(
        db.query(Trade.state, func.count(Trade.id))
        .filter(Trade.tenant_id == tenant_id, Trade.account_id == account_id)
        .group_by(Trade.state)
        .all()
    )

    trades_by_security = dict(
        db.query(Trade.security, func.count(Trade.id))
        .filter(Trade.tenant_id == tenant_id, Trade.account_id == account_id)
        .group_by(Trade.security)
        .all()
    )

    statistics = {
        "accountId": account_id,
        "totalTrades": total_trades,
        "averageQuantity": round(float(avg_quantity), 2),
        "buyCount": buy_count,
        "sellCount": sell_count,
        "tradesByState": trades_by_state,
        "tradesBySecurity": trades_by_security,
    }

    logger.info(
        "account_trade_statistics_generated",
        extra={
            "tenant_id": tenant_id,
            "account_id": account_id,
            "total_trades": total_trades,
        },
    )
    return statistics
