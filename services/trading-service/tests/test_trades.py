"""Test Trade operations."""
from unittest.mock import patch, AsyncMock


def test_list_trades_empty(client):
    response = client.get("/trades/")
    assert response.status_code == 200
    assert response.json() == []


@patch("app.service.validate_account_exists", new_callable=AsyncMock, return_value=True)
@patch("app.service.validate_security_exists", new_callable=AsyncMock, return_value=True)
def test_submit_trade(mock_security, mock_account, client):
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
    assert data["trade"]["quantity"] == 100
    assert data["trade"]["state"] == "Settled"


@patch("app.service.validate_account_exists", new_callable=AsyncMock, return_value=True)
@patch("app.service.validate_security_exists", new_callable=AsyncMock, return_value=True)
def test_submit_trade_creates_position(mock_security, mock_account, client):
    response = client.post("/trade/", json={
        "accountId": 1,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 50,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["position"]["quantity"] == 50


def test_submit_trade_invalid_side(client):
    response = client.post("/trade/", json={
        "accountId": 1,
        "security": "AAPL",
        "side": "Invalid",
        "quantity": 100,
    })
    assert response.status_code == 400


@patch("app.service.validate_account_exists", new_callable=AsyncMock, return_value=False)
def test_submit_trade_account_not_found(mock_account, client):
    response = client.post("/trade/", json={
        "accountId": 999,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert response.status_code == 400
    assert "Account" in response.json()["detail"]


def test_tenant_mismatch_rejected(client):
    response = client.get("/trades/", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
