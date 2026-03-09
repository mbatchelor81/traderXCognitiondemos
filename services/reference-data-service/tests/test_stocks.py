"""Test stock reference data operations."""


def test_list_stocks(client):
    response = client.get("/stocks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "ticker" in data[0]
    assert "companyName" in data[0]


def test_get_stock_by_ticker(client):
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


def test_get_stock_not_found(client):
    response = client.get("/stocks/INVALID_TICKER_XYZ")
    assert response.status_code == 404


def test_tenant_mismatch_rejected(client):
    response = client.get("/stocks/", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
