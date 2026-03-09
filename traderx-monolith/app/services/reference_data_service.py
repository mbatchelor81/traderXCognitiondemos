"""
Reference Data Service - stock ticker lookup.

Thin wrapper around the CSV-loaded stock data from helpers.
"""

import logging
from typing import List, Optional

from app.utils.helpers import load_stocks_from_csv, find_stock_by_ticker

logger = logging.getLogger(__name__)


def get_all_stocks() -> List[dict]:
    """Return all loaded stock records."""
    return load_stocks_from_csv()


def get_stock(ticker: str) -> Optional[dict]:
    """Look up a single stock by ticker symbol."""
    return find_stock_by_ticker(ticker)


def search_stocks(query: str, limit: int = 20) -> List[dict]:
    """Search stocks by ticker or company name."""
    if not query or len(query) < 1:
        return []
    query_lower = query.lower()
    results = []
    for stock in load_stocks_from_csv():
        if (query_lower in stock["ticker"].lower() or
                query_lower in stock["companyName"].lower()):
            results.append(stock)
            if len(results) >= limit:
                break
    return results
