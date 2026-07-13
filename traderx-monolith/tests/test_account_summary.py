"""Tests for the account summary statistics endpoint."""


def _create_account(client):
    resp = client.post("/account/", json={"displayName": "Summary Account"})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_account_summary_empty(client):
    """A new account has zeroed statistics."""
    account_id = _create_account(client)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["accountId"] == account_id
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_reflects_trades(client):
    """Statistics reflect trades submitted for the account."""
    account_id = _create_account(client)

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
        "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["settledTrades"] + data["pendingTrades"] == 2


def test_account_summary_not_found(client):
    """Requesting a non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
