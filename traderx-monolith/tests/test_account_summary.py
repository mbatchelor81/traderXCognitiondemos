"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify the summary endpoint returns aggregated trade statistics."""
    # Create an account
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Buy",
        "quantity": 50,
    })

    # Fetch summary
    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 150


def test_account_summary_with_buy_and_sell(client):
    """Verify summary correctly counts buy and sell trades."""
    acct = client.post("/account/", json={"displayName": "Buy Sell Account"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 200,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] == 200
    assert data["totalSellQuantity"] == 50
    assert data["netQuantity"] == 150


def test_account_summary_not_found(client):
    """Verify 404 for non-existent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
