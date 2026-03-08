"""Reference data (stocks) endpoints for Trades Service."""

import logging

from fastapi import APIRouter, HTTPException

from app.utils.helpers import load_stocks_from_csv, find_stock_by_ticker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stocks/")
def list_all_stocks():
    """Get all S&P 500 stocks."""
    stocks = load_stocks_from_csv()
    return stocks


@router.get("/stocks/{ticker}")
def get_stock_by_ticker(ticker: str):
    """Get a single stock by ticker symbol."""
    stock = find_stock_by_ticker(ticker)
    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f'Stock ticker "{ticker}" not found.'
        )
    return stock
