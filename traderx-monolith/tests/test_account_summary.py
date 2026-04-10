"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns trade statistics after creating trades."""
    # Create an account
    acct = client.post("/account/", json={"displayName": "Summary Test Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades
    for ticker, side, qty in [("AAPL", "Buy", 100), ("MSFT", "Buy", 50)]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": ticker,
            "side": side,
            "quantity": qty,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    # Fetch summary
    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200

    data = summary.json()
    stats = data["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] >= 0
    assert stats["pendingTrades"] >= 0
    assert stats["totalBuyQuantity"] >= 150
    assert "netQuantity" in stats


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
