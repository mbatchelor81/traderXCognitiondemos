"""Test trade endpoints for trades-service."""
from unittest.mock import AsyncMock, patch


def test_list_trades_empty(client):
    response = client.get("/trades/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_trades_by_account_empty(client):
    response = client.get("/trades/12345")
    assert response.status_code == 200
    assert response.json() == []


@patch("app.services.trade_processor.validate_account_exists", new_callable=AsyncMock, return_value=True)
def test_submit_trade_success(mock_validate, client):
    response = client.post("/trade/", json={
        "accountId": 22214,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["trade"]["accountId"] == 22214
    assert data["trade"]["security"] == "AAPL"
    assert data["trade"]["side"] == "Buy"
    assert data["trade"]["quantity"] == 100


@patch("app.services.trade_processor.validate_account_exists", new_callable=AsyncMock, return_value=True)
def test_submit_trade_creates_position(mock_validate, client):
    client.post("/trade/", json={
        "accountId": 22214,
        "security": "MSFT",
        "side": "Buy",
        "quantity": 50,
    })
    response = client.get("/positions/22214")
    assert response.status_code == 200
    positions = response.json()
    assert len(positions) == 1
    assert positions[0]["security"] == "MSFT"
    assert positions[0]["quantity"] == 50


@patch("app.services.trade_processor.validate_account_exists", new_callable=AsyncMock, return_value=False)
def test_submit_trade_invalid_account(mock_validate, client):
    response = client.post("/trade/", json={
        "accountId": 99999,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert response.status_code == 400


def test_submit_trade_invalid_side(client):
    response = client.post("/trade/", json={
        "accountId": 22214,
        "security": "AAPL",
        "side": "InvalidSide",
        "quantity": 100,
    })
    assert response.status_code == 400


def test_submit_trade_invalid_quantity(client):
    response = client.post("/trade/", json={
        "accountId": 22214,
        "security": "AAPL",
        "side": "Buy",
        "quantity": -10,
    })
    assert response.status_code == 400


def test_tenant_mismatch_rejected(client):
    response = client.get("/health", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
