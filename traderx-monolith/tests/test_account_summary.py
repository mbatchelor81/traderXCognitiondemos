"""Tests for GET /account/{account_id}/summary endpoint."""
import pytest


def _create_account(client, name="Test Account"):
    resp = client.post("/account/", json={"displayName": name})
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100):
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    return resp.json()


def test_summary_no_trades(client):
    """Summary for a fresh account should report all zeros."""
    account_id = _create_account(client)
    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 0
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 0


def test_summary_after_buy_trades(client):
    """Summary should reflect settled buy trades."""
    account_id = _create_account(client)
    _submit_trade(client, account_id, "AAPL", "Buy", 100)
    _submit_trade(client, account_id, "MSFT", "Buy", 50)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["settledTrades"] == 2
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 150


def test_summary_buy_and_sell(client):
    """Net quantity should account for both buys and sells."""
    account_id = _create_account(client)
    _submit_trade(client, account_id, "AAPL", "Buy", 200)
    _submit_trade(client, account_id, "AAPL", "Sell", 50)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] == 200
    assert data["totalSellQuantity"] == 50
    assert data["netQuantity"] == 150


def test_summary_nonexistent_account(client):
    """Requesting summary for a missing account should return 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
