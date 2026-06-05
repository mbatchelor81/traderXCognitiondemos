"""Tests for the account summary statistics endpoint."""


def test_account_summary_aggregates_trades(client):
    """Summary endpoint returns aggregated trade statistics for an account."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Sell", "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert "statistics" in body
    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    for key in ("settledTrades", "pendingTrades", "netQuantity"):
        assert key in stats


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
