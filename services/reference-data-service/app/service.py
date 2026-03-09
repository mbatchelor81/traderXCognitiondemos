"""Reference data service - loads stock tickers from CSV."""
import csv
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_stocks: Dict[str, Dict] = {}


def load_stocks_from_csv() -> None:
    """Load S&P 500 stock data from CSV file."""
    global _stocks
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sp500.csv")
    if not os.path.exists(csv_path):
        logger.warning("Stock data CSV not found at %s", csv_path)
        return
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("Symbol", row.get("symbol", "")).strip()
            if ticker:
                _stocks[ticker] = {
                    "Symbol": ticker,
                    "CompanyName": row.get("Security", row.get("Name", row.get("CompanyName", ""))),
                    "Sector": row.get("GICS Sector", row.get("Sector", "")),
                }
    logger.info("Loaded %d stocks from CSV", len(_stocks))


def get_all_stocks() -> List[Dict]:
    return list(_stocks.values())


def get_stock_by_ticker(ticker: str) -> Optional[Dict]:
    return _stocks.get(ticker.upper()) or _stocks.get(ticker)
