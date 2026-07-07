"""Tests for the account summary statistics endpoint."""


def test_account_summary_empty(client):
    """A new account with no trades returns zeroed statistics."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_reflects_trades(client):
    """Statistics reflect trades submitted for the account."""
    acct = client.post("/account/", json={"displayName": "Active Account"})
    account_id = acct.json()["id"]

    for security, side, qty in [("AAPL", "Buy", 100), ("MSFT", "Buy", 50)]:
        r = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": qty,
        })
        assert r.status_code == 200

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalTrades"] == stats["settledTrades"] + stats["pendingTrades"]


def test_account_summary_not_found(client):
    """A non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_tenant_isolation(client):
    """An account created in one tenant is not visible in another."""
    acct = client.post("/account/", json={"displayName": "Tenant A Account"},
                       headers={"X-Tenant-ID": "acme_corp"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary",
                      headers={"X-Tenant-ID": "globex_inc"})
    assert resp.status_code == 404
