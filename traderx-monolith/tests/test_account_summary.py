"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns trade statistics after submitting trades."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a couple of trades so there is data to aggregate
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT",
        "side": "Sell", "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200

    data = resp.json()
    assert "totalTrades" in data
    assert data["totalTrades"] >= 2
    assert "settledTrades" in data
    assert "pendingTrades" in data
    assert "netQuantity" in data


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
