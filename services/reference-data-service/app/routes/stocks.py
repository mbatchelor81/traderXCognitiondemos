"""Stock / reference data endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from app.services import stock_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stocks/")
def list_stocks():
    return stock_service.get_all_stocks()


@router.get("/stocks/{ticker}")
def get_stock(ticker: str):
    stock = stock_service.find_stock_by_ticker(ticker)
    if stock is None:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return stock
