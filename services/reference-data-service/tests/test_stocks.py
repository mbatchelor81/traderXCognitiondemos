"""Tests for Reference Data Service."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "reference-data-service"
    assert data["tenant"] == "test_tenant"


def test_list_stocks(client):
    response = client.get("/stocks/")
    assert response.status_code == 200
    stocks = response.json()
    assert isinstance(stocks, list)
    assert len(stocks) > 0


def test_get_stock_by_ticker(client):
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


def test_get_stock_not_found(client):
    response = client.get("/stocks/INVALID_TICKER_XYZ")
    assert response.status_code == 404
