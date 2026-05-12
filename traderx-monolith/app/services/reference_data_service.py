"""
Reference Data service — loads and queries S&P 500 stock data from CSV.
Extracted from app.utils.helpers to align with the target microservice
boundary defined in TARGET_ARCHITECTURE_CONSTRAINTS.md §7.
"""

import csv
import logging
from typing import List, Optional

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.models.stock import Stock

logger = logging.getLogger(__name__)

_stocks: Optional[List[Stock]] = None


def _ensure_loaded(file_path: Optional[str] = None):
    """Ensure stock data is loaded into memory from CSV."""
    global _stocks
    if _stocks is not None:
        return

    if file_path is None:
        file_path = REFERENCE_DATA_FILE

    stocks: List[Stock] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks.append(Stock.from_csv_row(row))
        _stocks = stocks
        logger.info("Reference data service loaded %d stocks from %s",
                     len(stocks), file_path)
    except FileNotFoundError:
        logger.error("Stock data file not found: %s", file_path)
        _stocks = []
    except Exception as e:
        logger.error("Error loading stock data: %s", str(e))
        _stocks = []


def get_all_stocks() -> List[Stock]:
    """Return all S&P 500 stocks."""
    _ensure_loaded()
    return _stocks or []


def find_stock_by_ticker(ticker: str) -> Optional[Stock]:
    """Find a single stock by exact ticker symbol."""
    _ensure_loaded()
    for stock in (_stocks or []):
        if stock.ticker == ticker:
            return stock
    return None


def search_stocks(query: str, limit: int = 20) -> List[Stock]:
    """Search stocks by ticker or company name (case-insensitive substring match)."""
    _ensure_loaded()
    if not query or len(query) < 1:
        return []

    query_lower = query.lower()
    results: List[Stock] = []
    for stock in (_stocks or []):
        if (query_lower in stock.ticker.lower()
                or query_lower in stock.company_name.lower()):
            results.append(stock)
            if len(results) >= limit:
                break
    return results


def clear_cache():
    """Clear the in-memory stocks cache. Useful for testing."""
    global _stocks
    _stocks = None
