"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_no_trades(client):
    """Summary for an account with no trades should return all zeros."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 0
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_with_trades(client):
    """Summary should reflect trade statistics after submitting trades."""
    acct = client.post("/account/", json={"displayName": "Active Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit two buy trades
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

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["settledTrades"] == 2
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 150


def test_account_summary_not_found(client):
    """Summary for a non-existent account should return 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
