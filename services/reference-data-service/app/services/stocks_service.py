"""
Stock reference data loaded once at startup from a static CSV.

The catalogue is immutable: it is read from disk by :func:`load_catalogue` and
handed to callers as read-only tuples/mappings, so no module elsewhere can
mutate the shared reference data.
"""

from __future__ import annotations

import csv
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

from app.config import REFERENCE_DATA_FILE, TENANT_ID
from app.logging_config import get_logger

logger = get_logger(__name__)

Stock = Mapping[str, str]

_catalogue: Sequence[Stock] = ()
_by_ticker: Mapping[str, Stock] = MappingProxyType({})


def load_catalogue(file_path: Optional[str] = None) -> Sequence[Stock]:
    """Read the CSV into the immutable in-memory catalogue. Called at startup."""
    global _catalogue, _by_ticker

    path = file_path or REFERENCE_DATA_FILE
    stocks: list[Stock] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks.append(
                    MappingProxyType(
                        {
                            "ticker": row.get("Symbol", ""),
                            "companyName": row.get("Security", ""),
                        }
                    )
                )
        logger.info(
            "reference_data_loaded",
            extra={"stock_count": len(stocks), "file_path": path, "tenant_id": TENANT_ID},
        )
    except FileNotFoundError:
        logger.error("reference_data_file_missing", extra={"file_path": path})
    except Exception as exc:  # noqa: BLE001 — mirrors the monolith's tolerance
        logger.error(
            "reference_data_load_failed",
            extra={"file_path": path, "error": str(exc)},
        )

    _catalogue = tuple(stocks)
    _by_ticker = MappingProxyType({stock["ticker"]: stock for stock in _catalogue})
    return _catalogue


def list_stocks(
    tenant_id: str,
    search: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """
    Return the stock catalogue, optionally filtered by a case-insensitive
    substring of the ticker or company name and truncated to ``limit`` rows.
    """
    stocks = _catalogue
    if search:
        needle = search.lower()
        stocks = tuple(
            stock
            for stock in stocks
            if needle in stock["ticker"].lower()
            or needle in stock["companyName"].lower()
        )
    if limit is not None:
        stocks = stocks[:limit]

    logger.info(
        "stocks_listed",
        extra={
            "tenant_id": tenant_id,
            "search": search,
            "limit": limit,
            "result_count": len(stocks),
        },
    )
    return [dict(stock) for stock in stocks]


def find_stock_by_ticker(tenant_id: str, ticker: str) -> Optional[dict]:
    """Find a single stock by exact ticker symbol, or None when unknown."""
    stock = _by_ticker.get(ticker)
    if stock is None:
        logger.info("stock_not_found", extra={"tenant_id": tenant_id, "ticker": ticker})
        return None
    return dict(stock)


def stock_count() -> int:
    """Number of stocks currently loaded."""
    return len(_catalogue)
