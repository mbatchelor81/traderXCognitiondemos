"""
Reference Data (stocks) endpoints.
Delegates to reference_data_service for all business logic.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.services import reference_data_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stocks/")
def list_all_stocks():
    """
    Get all S&P 500 stocks.
    Mirrors reference-data StocksController.findAll().
    """
    stocks = reference_data_service.get_all_stocks()
    return [s.to_dict() for s in stocks]


@router.get("/stocks/search")
def search_stocks(q: str = Query(..., min_length=1),
                  limit: int = Query(20, ge=1, le=100)):
    """
    Search stocks by ticker or company name.
    Returns up to `limit` matches for the query string.
    """
    results = reference_data_service.search_stocks(q, limit)
    return [s.to_dict() for s in results]


@router.get("/stocks/{ticker}")
def get_stock_by_ticker(ticker: str):
    """
    Get a single stock by ticker symbol.
    Mirrors reference-data StocksController.findByTicker().
    """
    stock = reference_data_service.find_stock_by_ticker(ticker)
    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f'Stock ticker "{ticker}" not found.'
        )
    return stock.to_dict()
