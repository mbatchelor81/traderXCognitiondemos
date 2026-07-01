"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify summary endpoint returns aggregated trade statistics."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades so statistics are non-trivial
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

    body = resp.json()
    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    assert "settledTrades" in stats
    assert "pendingTrades" in stats
    assert "netQuantity" in stats
    assert "totalBuyQuantity" in stats
    assert "totalSellQuantity" in stats


def test_account_summary_not_found(client):
    """Verify 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
