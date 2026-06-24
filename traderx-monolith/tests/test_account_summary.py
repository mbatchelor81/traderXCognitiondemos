"""Tests for the account summary statistics endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint aggregates trade statistics for an account."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    for payload in [
        {"accountId": account_id, "security": "AAPL", "side": "Buy", "quantity": 100},
        {"accountId": account_id, "security": "MSFT", "side": "Buy", "quantity": 50},
        {"accountId": account_id, "security": "AAPL", "side": "Sell", "quantity": 30},
    ]:
        assert client.post("/trade/", json=payload).status_code == 200

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 3
    assert stats["settledTrades"] + stats["pendingTrades"] <= stats["totalTrades"]
    assert stats["netQuantity"] == stats["totalBuyQuantity"] - stats["totalSellQuantity"]


def test_account_summary_unknown_account_returns_404(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
