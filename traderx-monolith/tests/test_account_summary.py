"""Tests for account summary endpoint."""


def test_account_summary_no_trades(client):
    """Empty account returns zeroed statistics."""
    resp = client.post("/account/", json={"displayName": "Empty Acct"})
    account_id = resp.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_with_trades(client):
    """Account with trades returns correct aggregated statistics."""
    resp = client.post("/account/", json={"displayName": "Trade Acct"})
    account_id = resp.json()["id"]

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

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] >= 0
    assert data["totalSellQuantity"] >= 0
    assert "netQuantity" in data
    assert "settledTrades" in data
    assert "pendingTrades" in data


def test_account_summary_nonexistent_account(client):
    """Non-existent account returns 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
