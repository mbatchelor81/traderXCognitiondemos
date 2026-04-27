"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_summary_returns_statistics_after_trades(client):
    """Summary endpoint returns correct aggregated trade stats."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT",
        "side": "Sell", "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200

    data = resp.json()
    assert data["totalTrades"] == 2
    assert "settledTrades" in data
    assert "pendingTrades" in data
    assert "totalBuyQuantity" in data
    assert "totalSellQuantity" in data
    assert "netQuantity" in data


def test_summary_empty_account(client):
    """Summary on an account with no trades returns zeroes."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200

    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_summary_not_found(client):
    """Summary on a non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
