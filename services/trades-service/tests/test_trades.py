"""Tests for trade and position operations."""
import asyncio
from unittest.mock import patch, AsyncMock


def test_list_trades_empty(client):
    """Test listing trades when none exist."""
    response = client.get("/trades/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_positions_empty(client):
    """Test listing positions when none exist."""
    response = client.get("/positions/")
    assert response.status_code == 200
    assert response.json() == []


def test_submit_trade_with_mocked_account_validation(client):
    """Test submitting a trade with mocked account validation (cross-service call)."""
    mock_validate = AsyncMock(return_value=True)
    with patch("app.services.trade_processor.validate_account_exists", mock_validate):
        response = client.post("/trade/", json={
            "accountId": 1,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trade"]["security"] == "AAPL"
        assert data["trade"]["side"] == "Buy"
        assert data["trade"]["quantity"] == 100
        assert data["position"]["security"] == "AAPL"
        assert data["position"]["quantity"] == 100


def test_submit_trade_invalid_side(client):
    """Test submitting a trade with invalid side."""
    response = client.post("/trade/", json={
        "accountId": 1,
        "security": "AAPL",
        "side": "Hold",
        "quantity": 100,
    })
    assert response.status_code == 400


def test_submit_trade_invalid_quantity(client):
    """Test submitting a trade with invalid quantity."""
    response = client.post("/trade/", json={
        "accountId": 1,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 0,
    })
    assert response.status_code == 400


def test_tenant_mismatch_rejected(client):
    """Test that mismatched tenant header is rejected with 403."""
    response = client.get("/health", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403


def test_reference_data_stocks(client):
    """Test listing stocks from reference data."""
    response = client.get("/stocks/")
    assert response.status_code == 200
    stocks = response.json()
    assert len(stocks) > 0
    assert "ticker" in stocks[0]


def test_reference_data_stock_by_ticker(client):
    """Test getting a stock by ticker."""
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


def test_reference_data_stock_not_found(client):
    """Test getting a non-existent stock."""
    response = client.get("/stocks/ZZZZZ")
    assert response.status_code == 404
