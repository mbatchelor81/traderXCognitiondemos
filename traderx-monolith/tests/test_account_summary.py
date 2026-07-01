"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns aggregated trade stats for an account."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades so the stats are non-trivial
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

    stats = resp.json()
    assert stats["totalTrades"] == 2
    assert "settledTrades" in stats
    assert "pendingTrades" in stats
    assert "totalBuyQuantity" in stats
    assert "totalSellQuantity" in stats
    assert "netQuantity" in stats


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
