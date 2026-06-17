"""Tests for reference data (stocks) endpoints and service."""
import pytest

from app.services import reference_data_service


@pytest.fixture(autouse=True)
def _clear_stock_cache():
    """Clear stock cache before each test so CSV is reloaded."""
    reference_data_service.clear_cache()
    yield
    reference_data_service.clear_cache()


# =============================================================================
# Endpoint Tests
# =============================================================================

def test_list_all_stocks(client):
    """GET /stocks/ returns the full S&P 500 list."""
    resp = client.get("/stocks/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "ticker" in first
    assert "companyName" in first


def test_get_stock_by_ticker_found(client):
    """GET /stocks/{ticker} returns the stock when it exists."""
    resp = client.get("/stocks/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["companyName"] == "Apple"


def test_get_stock_by_ticker_not_found(client):
    """GET /stocks/{ticker} returns 404 for unknown tickers."""
    resp = client.get("/stocks/ZZZZZ")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_search_stocks_by_ticker(client):
    """GET /stocks/search?q=AA returns stocks matching the ticker."""
    resp = client.get("/stocks/search", params={"q": "AAPL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    tickers = [s["ticker"] for s in data]
    assert "AAPL" in tickers


def test_search_stocks_by_company_name(client):
    """GET /stocks/search?q=Apple returns stocks matching the company name."""
    resp = client.get("/stocks/search", params={"q": "Apple"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any("Apple" in s["companyName"] for s in data)


def test_search_stocks_limit(client):
    """GET /stocks/search respects the limit parameter."""
    resp = client.get("/stocks/search", params={"q": "A", "limit": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 3


def test_search_stocks_no_match(client):
    """GET /stocks/search returns empty list for no matches."""
    resp = client.get("/stocks/search", params={"q": "xyznonexistent"})
    assert resp.status_code == 200
    assert resp.json() == []


# =============================================================================
# Service Layer Tests
# =============================================================================

def test_service_get_all_stocks():
    """reference_data_service.get_all_stocks() returns Stock objects."""
    stocks = reference_data_service.get_all_stocks()
    assert len(stocks) > 0
    assert stocks[0].ticker != ""
    assert stocks[0].company_name != ""


def test_service_find_stock_by_ticker():
    """reference_data_service.find_stock_by_ticker() returns the correct Stock."""
    stock = reference_data_service.find_stock_by_ticker("MSFT")
    assert stock is not None
    assert stock.ticker == "MSFT"
    assert stock.company_name == "Microsoft"


def test_service_find_stock_by_ticker_not_found():
    """reference_data_service.find_stock_by_ticker() returns None for unknown tickers."""
    stock = reference_data_service.find_stock_by_ticker("NOTREAL")
    assert stock is None


def test_service_search_stocks():
    """reference_data_service.search_stocks() matches by ticker and company name."""
    results = reference_data_service.search_stocks("Micro")
    assert len(results) >= 1
    assert any(s.ticker == "MSFT" for s in results)
