"""Reference Data Service route handlers."""
import logging
from fastapi import APIRouter, HTTPException

from app.service import get_all_stocks, get_stock_by_ticker

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stocks/")
def list_stocks():
    return get_all_stocks()


@router.get("/stocks/{ticker}")
def get_stock(ticker: str):
    stock = get_stock_by_ticker(ticker)
    if stock is None:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return stock
