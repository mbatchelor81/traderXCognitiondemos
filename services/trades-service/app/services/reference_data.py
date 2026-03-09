"""Reference data helpers for trades-service."""

import csv
import logging
from typing import List, Optional

from app.config import REFERENCE_DATA_FILE

logger = logging.getLogger(__name__)

_stocks_cache = None


def load_stocks_from_csv(file_path: Optional[str] = None) -> List[dict]:
    """Load S&P 500 stock data from CSV file. Results are cached."""
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
