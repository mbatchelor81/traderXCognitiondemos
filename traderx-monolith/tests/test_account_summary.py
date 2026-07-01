"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns correct aggregated trade statistics."""
    # Create an account
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a few trades
    for security, side, qty in [
        ("AAPL", "Buy", 100),
        ("AAPL", "Buy", 50),
        ("MSFT", "Buy", 200),
    ]:
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

    assert data["totalTrades"] == 3
    assert data["settledTrades"] == 3
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 350
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 350


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_with_mixed_sides(client):
    """Summary correctly accounts for both Buy and Sell trades."""
    acct = client.post("/account/", json={"displayName": "Mixed Trades"})
    account_id = acct.json()["id"]

    # Buy first so there's a position to sell against
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "GOOG",
        "side": "Buy",
        "quantity": 300,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "GOOG",
        "side": "Sell",
        "quantity": 100,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] == 300
    assert data["totalSellQuantity"] == 100
    assert data["netQuantity"] == 200
