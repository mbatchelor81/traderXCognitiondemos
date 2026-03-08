"""
Reference data (stocks) endpoints.
Ported from reference-data Node.js/NestJS implementation.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.config import TENANT_ID
from app.utils.helpers import load_stocks_from_csv, find_stock_by_ticker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stocks/")
def list_all_stocks():
    """
    Get all S&P 500 stocks.
    Mirrors reference-data StocksController.findAll().
    """
    stocks = load_stocks_from_csv()
    return stocks


@router.get("/stocks/{ticker}")
def get_stock_by_ticker(ticker: str):
    """
    Get a single stock by ticker symbol.
    Mirrors reference-data StocksController.findByTicker().
    """
    stock = find_stock_by_ticker(ticker)
    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f'Stock ticker "{ticker}" not found.'
        )
    return stock
