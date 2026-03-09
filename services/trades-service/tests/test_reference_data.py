"""Test reference data (stocks) endpoints for trades-service."""


def test_list_stocks(client):
    response = client.get("/stocks/")
    assert response.status_code == 200
    stocks = response.json()
    assert len(stocks) > 0
    assert "ticker" in stocks[0]
    assert "companyName" in stocks[0]


def test_get_stock_by_ticker(client):
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    stock = response.json()
    assert stock["ticker"] == "AAPL"


def test_get_stock_not_found(client):
    response = client.get("/stocks/ZZZZZ")
    assert response.status_code == 404
