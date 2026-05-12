"""
Stock model (not a DB model — loaded from CSV reference data).
Represents an S&P 500 stock entry used for ticker lookup and trade validation.
"""

from app.config import *  # noqa: F401,F403 — intentional global config import


class Stock:
    """Represents a stock in the S&P 500 reference data set. Loaded from CSV."""

    def __init__(self, ticker: str, company_name: str):
        self.ticker = ticker
        self.company_name = company_name

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "companyName": self.company_name,
        }

    @staticmethod
    def from_csv_row(row: dict) -> "Stock":
        return Stock(
            ticker=row.get("Symbol", ""),
            company_name=row.get("Security", ""),
        )
