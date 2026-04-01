"""Tests for the GET /account/{account_id}/summary endpoint."""
import pytest


def test_account_summary_returns_statistics(client):
    """Verify the summary endpoint returns aggregated trade statistics."""
    # Arrange — create an account and submit trades
    acct = client.post("/account/", json={"displayName": "Summary Test Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Buy",
        "quantity": 50,
    })

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] >= 0
    assert stats["pendingTrades"] >= 0
    assert stats["totalBuyQuantity"] >= 150
    assert stats["netQuantity"] >= 0
    assert "account" in body
    assert "positions" in body


def test_account_summary_not_found(client):
    """Verify the summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_buy_and_sell(client):
    """Verify net quantity reflects both buy and sell trades."""
    acct = client.post("/account/", json={"displayName": "Buy Sell Account"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 200,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 200
    assert stats["totalSellQuantity"] == 50
    assert stats["netQuantity"] == 150
