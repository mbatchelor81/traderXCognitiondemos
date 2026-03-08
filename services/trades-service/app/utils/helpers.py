"""Utility functions for Trades Service."""

import csv
import logging
from datetime import datetime
from typing import List, Optional

from app.config import REFERENCE_DATA_FILE, AUDIT_ENABLED

logger = logging.getLogger(__name__)

_stocks_cache = None


def load_stocks_from_csv(file_path: Optional[str] = None) -> List[dict]:
    """Load S&P 500 stock data from CSV file. Results are cached in memory."""
    global _stocks_cache
    if _stocks_cache is not None:
        return _stocks_cache

    if file_path is None:
        file_path = REFERENCE_DATA_FILE

    stocks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks.append({
                    "ticker": row.get("Symbol", ""),
                    "companyName": row.get("Security", ""),
                })
        _stocks_cache = stocks
        logger.info("Loaded %d stocks from %s", len(stocks), file_path)
    except FileNotFoundError:
        logger.error("Stock data file not found: %s", file_path)
    except Exception as e:
        logger.error("Error loading stock data: %s", str(e))

    return stocks


def find_stock_by_ticker(ticker: str) -> Optional[dict]:
    """Find a single stock by ticker symbol."""
    stocks = load_stocks_from_csv()
    for stock in stocks:
        if stock["ticker"] == ticker:
            return stock
    return None


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


def validate_trade_side(side: str) -> bool:
    """Validate that a trade side is either Buy or Sell."""
    return side in ("Buy", "Sell")


def validate_trade_quantity(quantity: int, min_qty: int, max_qty: int) -> bool:
    """Validate that trade quantity is within allowed range."""
    return min_qty <= quantity <= max_qty


def log_audit_event(event_type: str, tenant_id: str, details: str):
    """Log an audit event."""
    if not AUDIT_ENABLED:
        return
    timestamp = now_utc().isoformat()
    audit_msg = f"[AUDIT] [{timestamp}] [{tenant_id}] [{event_type}] {details}"
    logger.info(audit_msg)
