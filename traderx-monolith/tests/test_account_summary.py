"""Tests for the account summary statistics endpoint."""


def test_account_summary_empty(client):
    """A new account with no trades returns zeroed statistics."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_counts_trades(client):
    """Submitting trades is reflected in the aggregated statistics."""
    acct = client.post("/account/", json={"displayName": "Active Account"})
    account_id = acct.json()["id"]

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
    stats = resp.json()
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] + stats["pendingTrades"] == 2


def test_account_summary_not_found(client):
    """An unknown account id returns 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
