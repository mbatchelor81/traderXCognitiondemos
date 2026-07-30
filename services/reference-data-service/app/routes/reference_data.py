"""
Reference data (stocks) endpoints.
Ported from the TraderX monolith's app/routes/reference_data.py.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.services import stocks_service

router = APIRouter()


class StockResponse(BaseModel):
    """A single tradable security."""

    ticker: str = Field(..., description="Ticker symbol, e.g. 'AAPL'")
    companyName: str = Field(..., description="Company name, e.g. 'Apple Inc.'")


@router.get(
    "/stocks/",
    response_model=List[StockResponse],
    summary="List or search S&P 500 stocks",
)
def list_all_stocks(
    request: Request,
    search: Optional[str] = Query(
        None, description="Case-insensitive substring of ticker or company name"
    ),
    limit: Optional[int] = Query(
        None, ge=1, description="Maximum number of stocks to return"
    ),
) -> List[StockResponse]:
    """
    Get all S&P 500 stocks. With no query parameters this returns the full
    catalogue, matching the monolith's behaviour.
    """
    stocks = stocks_service.list_stocks(
        tenant_id=request.state.tenant_id, search=search, limit=limit
    )
    return [StockResponse(**stock) for stock in stocks]


@router.get(
    "/stocks/{ticker}",
    response_model=StockResponse,
    summary="Get a single stock by ticker",
    responses={404: {"description": "Ticker is not a known security"}},
)
def get_stock_by_ticker(request: Request, ticker: str) -> StockResponse:
    """Get a single stock by ticker symbol; 404 when the ticker is unknown."""
    stock = stocks_service.find_stock_by_ticker(request.state.tenant_id, ticker)
    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f'Stock ticker "{ticker}" not found.',
        )
    return StockResponse(**stock)
