"""Tests for the account summary statistics endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint aggregates trade statistics for an account."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT",
        "side": "Sell", "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["accountId"] == account_id
    stats = data["statistics"]
    for key in ("totalTrades", "settledTrades", "pendingTrades",
                "totalBuyQuantity", "totalSellQuantity", "netQuantity"):
        assert key in stats
    assert stats["totalTrades"] == 2


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for an unknown account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
