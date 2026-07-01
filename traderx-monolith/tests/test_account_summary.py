"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_empty(client):
    """Summary for an account with no trades returns zeroed statistics."""
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
    """Summary reflects trade counts after submitting trades."""
    acct = client.post("/account/", json={"displayName": "Active Account"})
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
        "side": "Sell",
        "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2


def test_account_summary_not_found(client):
    """Summary for a non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
