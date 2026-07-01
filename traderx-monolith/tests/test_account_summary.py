"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify summary endpoint returns aggregated trade statistics."""
    # Create an account
    acct = client.post("/account/", json={"displayName": "Summary Test Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a few trades
    for security, side, qty in [("AAPL", "Buy", 100), ("AAPL", "Buy", 50), ("MSFT", "Sell", 30)]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": qty,
        })
        assert resp.status_code == 200

    # Fetch the summary
    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    # Validate structure
    assert "account" in data
    assert "statistics" in data
    stats = data["statistics"]

    assert stats["totalTrades"] == 3
    assert stats["settledTrades"] == 3
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 30
    assert stats["netQuantity"] == 120


def test_account_summary_not_found(client):
    """Verify 404 for a non-existent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_account_summary_no_trades(client):
    """Verify summary returns zero stats for an account with no trades."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]

    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0
