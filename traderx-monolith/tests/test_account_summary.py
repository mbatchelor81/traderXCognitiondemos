"""Tests for the account summary statistics endpoint."""


def _create_account(client):
    resp = client.post("/account/", json={"displayName": "Summary Account"})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_account_summary_empty(client):
    """A brand new account has zeroed-out statistics."""
    account_id = _create_account(client)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_with_trades(client):
    """Statistics reflect submitted trades (buy/sell, settled, net quantity)."""
    account_id = _create_account(client)

    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Sell", "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 2
    # Trades auto-settle in the default tenant, so buy/sell quantities count.
    assert stats["totalBuyQuantity"] == 100
    assert stats["totalSellQuantity"] == 40
    assert stats["netQuantity"] == 60


def test_account_summary_not_found(client):
    """Requesting a summary for a non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_tenant_isolation(client):
    """An account created in one tenant is not visible from another tenant."""
    resp = client.post("/account/", json={"displayName": "Acme Account"},
                       headers={"X-Tenant-ID": "acme_corp"})
    account_id = resp.json()["id"]

    other = client.get(f"/account/{account_id}/summary",
                       headers={"X-Tenant-ID": "globex_inc"})
    assert other.status_code == 404
