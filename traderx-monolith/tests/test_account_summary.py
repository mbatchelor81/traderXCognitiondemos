"""Tests for the GET /account/{account_id}/summary endpoint."""
import pytest


def _create_account(client, name: str = "Test Account") -> int:
    resp = client.post("/account/", json={"displayName": name})
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id: int, security: str, side: str, quantity: int):
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    return resp.json()


def test_summary_returns_statistics(client):
    """Summary endpoint returns expected statistic fields."""
    account_id = _create_account(client)
    _submit_trade(client, account_id, "AAPL", "Buy", 100)
    _submit_trade(client, account_id, "MSFT", "Sell", 50)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200

    data = resp.json()
    assert "totalTrades" in data
    assert "settledTrades" in data
    assert "pendingTrades" in data
    assert "netQuantity" in data
    assert data["totalTrades"] >= 2


def test_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_summary_empty_account(client):
    """Summary endpoint returns zeros when the account has no trades."""
    account_id = _create_account(client)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200

    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0
