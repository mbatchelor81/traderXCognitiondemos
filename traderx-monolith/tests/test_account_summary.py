"""Tests for the account summary statistics endpoint."""


def test_account_summary_returns_statistics(client):
    """GET /account/{id}/summary returns aggregated trade stats."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a trade so there is data to aggregate
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert "totalTrades" in data
    assert "settledTrades" in data
    assert "pendingTrades" in data
    assert "netQuantity" in data
    assert data["totalTrades"] >= 1


def test_account_summary_not_found(client):
    """GET /account/{id}/summary returns 404 for missing account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
