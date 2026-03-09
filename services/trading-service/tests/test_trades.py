"""Tests for Trading Service."""
from unittest.mock import patch


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "trading-service"
    assert data["tenant"] == "test_tenant"


@patch("app.services.trade_processor._validate_account", return_value=True)
@patch("app.services.trade_processor._validate_security", return_value=True)
@patch("app.services.trade_processor._update_position", return_value={"quantity": 100})
def test_submit_trade(mock_pos, mock_sec, mock_acct, client):
    response = client.post("/trade/", json={
        "accountId": 1001,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["trade"]["security"] == "AAPL"
    assert data["trade"]["state"] == "Settled"


def test_list_trades_empty(client):
    response = client.get("/trades/")
    assert response.status_code == 200
    assert response.json() == []


@patch("app.services.trade_processor._validate_account", return_value=True)
@patch("app.services.trade_processor._validate_security", return_value=True)
@patch("app.services.trade_processor._update_position", return_value={"quantity": 50})
def test_submit_trade_and_list(mock_pos, mock_sec, mock_acct, client):
    client.post("/trade/", json={
        "accountId": 2001, "security": "MSFT", "side": "Buy", "quantity": 50,
    })
    response = client.get("/trades/2001")
    assert response.status_code == 200
    trades = response.json()
    assert len(trades) == 1
    assert trades[0]["security"] == "MSFT"


def test_submit_trade_invalid_side(client):
    response = client.post("/trade/", json={
        "accountId": 1001, "security": "AAPL", "side": "Short", "quantity": 100,
    })
    assert response.status_code == 400
