"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify summary endpoint returns aggregated trade statistics."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a few trades
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT",
        "side": "Buy", "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    stats = data["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] == 2
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 150


def test_account_summary_not_found(client):
    """Verify summary returns 404 for a non-existent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
