"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_empty_account(client):
    """Summary for an account with no trades returns all-zero statistics."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_with_trades(client):
    """Summary reflects trade statistics after submitting trades."""
    acct = client.post("/account/", json={"displayName": "Active Account"})
    account_id = acct.json()["id"]

    # Submit a buy trade
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    # Submit a sell trade
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] >= 0
    assert data["totalSellQuantity"] >= 0
    assert data["netQuantity"] == data["totalBuyQuantity"] - data["totalSellQuantity"]


def test_account_summary_not_found(client):
    """Summary for a non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
