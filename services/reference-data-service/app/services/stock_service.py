"""Stock data service — loads S&P 500 data from CSV."""

import csv
import logging
import os
from typing import Dict, List, Optional

from app.config import DATA_DIR

logger = logging.getLogger(__name__)

_stocks: List[Dict[str, str]] = []
_stocks_by_ticker: Dict[str, Dict[str, str]] = {}


def load_stocks():
    """Load stocks from CSV file into memory."""
    global _stocks, _stocks_by_ticker
    csv_path = os.path.join(DATA_DIR, "s-and-p-500-companies.csv")
    if not os.path.exists(csv_path):
        logger.warning("Stock CSV not found at %s", csv_path)
        return

    _stocks = []
    _stocks_by_ticker = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("Symbol", row.get("symbol", "")).strip()
            if ticker:
                stock = {
                    "ticker": ticker,
                    "companyName": row.get("Name", row.get("name", "")),
                    "sector": row.get("Sector", row.get("sector", "")),
                }
                _stocks.append(stock)
                _stocks_by_ticker[ticker.upper()] = stock

    logger.info("Loaded %d stocks from CSV", len(_stocks))


def get_all_stocks() -> List[Dict[str, str]]:
    return _stocks


def find_stock_by_ticker(ticker: str) -> Optional[Dict[str, str]]:
    return _stocks_by_ticker.get(ticker.upper())
