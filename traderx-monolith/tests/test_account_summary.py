"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns correct trade statistics for an account."""
    # Create an account
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a few trades
    for security, side, qty in [
        ("AAPL", "Buy", 100),
        ("MSFT", "Buy", 50),
        ("AAPL", "Sell", 30),
    ]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": qty,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    # Fetch summary
    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200
    data = summary.json()

    assert data["totalTrades"] == 3
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 30
    assert data["netQuantity"] == 120
    # All trades auto-settle for acme_corp (default tenant)
    assert data["settledTrades"] == 3
    assert data["pendingTrades"] == 0


def test_account_summary_empty_account(client):
    """Summary endpoint returns zeroes for an account with no trades."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200
    data = summary.json()

    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 0
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a nonexistent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
