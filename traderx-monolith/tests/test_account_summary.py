"""Tests for the account summary statistics endpoint."""
import pytest


def test_account_summary_with_trades(client):
    """Test that summary returns correct stats after submitting trades."""
    # Arrange — create account and submit trades
    acct = client.post("/account/", json={"displayName": "Summary Test"})
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
        "side": "Sell",
        "quantity": 50,
    })

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert "settledTrades" in data
    assert "pendingTrades" in data
    assert "totalBuyQuantity" in data
    assert "totalSellQuantity" in data
    assert "netQuantity" in data


def test_account_summary_empty_account(client):
    """Test summary for an account with no trades."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")

    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_not_found(client):
    """Test summary for a non-existent account returns 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
