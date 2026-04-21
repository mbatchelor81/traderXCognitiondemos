"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns correct trade statistics after trades."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a few trades
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
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 30,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 3
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 30
    assert data["netQuantity"] == 120
    assert "settledTrades" in data
    assert "pendingTrades" in data


def test_account_summary_empty_account(client):
    """Summary returns zeroed statistics for an account with no trades."""
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


def test_account_summary_not_found(client):
    """Summary returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
