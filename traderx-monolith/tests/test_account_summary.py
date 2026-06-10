"""Tests for the account summary endpoint."""
import pytest


def test_account_summary_empty(client):
    """Summary for an account with no trades returns zeroed statistics."""
    account_resp = client.post("/account/", json={"displayName": "Summary Acct"})
    account_id = account_resp.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["account"]["id"] == account_id
    stats = data["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 0
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_with_trades(client):
    """Summary aggregates trade statistics for the account.

    acme_corp (default tenant) auto-settles trades, so submitted trades land
    in the Settled state and contribute to settled/buy/sell quantities.
    """
    account_resp = client.post("/account/", json={"displayName": "Summary Acct"})
    account_id = account_resp.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL", "side": "Buy", "quantity": 100
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT", "side": "Sell", "quantity": 40
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]

    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] == 2
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 100
    assert stats["totalSellQuantity"] == 40
    assert stats["netQuantity"] == 60


def test_account_summary_nonexistent_account(client):
    """Summary for a non-existent account returns 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
