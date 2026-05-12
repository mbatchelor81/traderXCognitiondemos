"""Integration tests for GET /account/{account_id}/summary endpoint."""


def test_summary_empty_account(client):
    """Summary for a new account with no trades or positions."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["accountId"] == account_id
    assert data["displayName"] == "Empty Account"
    assert data["tradeCount"] == 0
    assert data["totalPositionQuantity"] == 0


def test_summary_not_found(client):
    """Summary for a non-existent account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_summary_with_trades(client):
    """Summary reflects trade count after submitting trades."""
    acct = client.post("/account/", json={"displayName": "Trade Account"})
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
    data = resp.json()
    assert data["tradeCount"] == 2
    assert data["totalPositionQuantity"] == 150


def test_summary_buy_and_sell(client):
    """Summary correctly aggregates positions after buy and sell trades."""
    acct = client.post("/account/", json={"displayName": "Mixed Account"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 200,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tradeCount"] == 2
    assert data["totalPositionQuantity"] == 150


def test_summary_tenant_isolation(client):
    """Account in tenant A is not visible from tenant B."""
    acct = client.post(
        "/account/",
        json={"displayName": "Tenant A Account"},
        headers={"X-Tenant-ID": "acme_corp"},
    )
    account_id = acct.json()["id"]

    resp = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "globex_inc"},
    )
    assert resp.status_code == 404
