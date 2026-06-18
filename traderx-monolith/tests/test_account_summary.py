"""Tests for the account summary statistics endpoint."""
import pytest


def test_get_account_summary_empty(client):
    """An account with no trades returns zeroed statistics."""
    account_id = client.post(
        "/account/", json={"displayName": "Summary Account"}
    ).json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["accountId"] == account_id
    assert data["displayName"] == "Summary Account"
    stats = data["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 0
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 0


def test_get_account_summary_with_trades(client):
    """Statistics reflect submitted (auto-settled) trades."""
    account_id = client.post(
        "/account/", json={"displayName": "Active Account"}
    ).json()["id"]

    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 50,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT",
        "side": "Sell", "quantity": 30,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]

    assert stats["totalTrades"] == 3
    assert stats["settledTrades"] == 3
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 30
    assert stats["netQuantity"] == 120


def test_get_account_summary_nonexistent_account(client):
    """A missing account returns 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
