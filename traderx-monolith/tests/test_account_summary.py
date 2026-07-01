"""Integration tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_with_trades(client):
    """Verify summary returns correct statistics after submitting trades."""
    # Create an account
    acct = client.post("/account/", json={"displayName": "Summary Test Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a few trades
    for security, side, qty in [("AAPL", "Buy", 100), ("MSFT", "Buy", 50), ("AAPL", "Buy", 25)]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": qty,
        })
        assert resp.status_code == 200

    # Fetch summary
    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200
    data = summary.json()

    assert data["totalTrades"] == 3
    assert data["settledTrades"] == 3
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 175
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 175


def test_account_summary_empty_account(client):
    """Summary for an account with no trades should return all zeros."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200
    data = summary.json()

    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_not_found(client):
    """Summary for a non-existent account should return 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
