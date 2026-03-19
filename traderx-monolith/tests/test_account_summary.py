"""Integration tests for the GET /account/{account_id}/summary endpoint."""

TENANT_HEADER = {"X-Tenant-ID": "test_tenant"}


def _create_account(client, name="Test Account"):
    resp = client.post(
        "/account/", json={"displayName": name}, headers=TENANT_HEADER
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100):
    resp = client.post(
        "/trade/",
        json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
        },
        headers=TENANT_HEADER,
    )
    assert resp.status_code == 200
    return resp.json()


def test_summary_returns_zeros_for_new_account(client):
    """A freshly-created account with no trades should return all-zero stats."""
    account_id = _create_account(client)

    resp = client.get(
        f"/account/{account_id}/summary", headers=TENANT_HEADER
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 0
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 0


def test_summary_reflects_submitted_trades(client):
    """After submitting trades the summary stats should reflect them."""
    account_id = _create_account(client)

    _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100)
    _submit_trade(client, account_id, security="MSFT", side="Sell", quantity=50)

    resp = client.get(
        f"/account/{account_id}/summary", headers=TENANT_HEADER
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 2
    # Trades settle immediately in-process, so settled should be 2
    assert data["settledTrades"] == 2
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 100
    assert data["totalSellQuantity"] == 50
    assert data["netQuantity"] == 50


def test_summary_404_for_nonexistent_account(client):
    """Requesting summary for an account that doesn't exist returns 404."""
    resp = client.get("/account/99999/summary", headers=TENANT_HEADER)
    assert resp.status_code == 404


def test_summary_tenant_isolation(client):
    """Accounts from one tenant should not appear in another tenant's summary."""
    # Create account in tenant A
    resp_a = client.post(
        "/account/",
        json={"displayName": "Tenant A Account"},
        headers={"X-Tenant-ID": "tenant_a"},
    )
    account_id = resp_a.json()["id"]

    # Submit a trade in tenant A
    client.post(
        "/trade/",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 200,
        },
        headers={"X-Tenant-ID": "tenant_a"},
    )

    # Query summary from tenant B — should 404 because account doesn't exist for tenant B
    resp_b = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "tenant_b"},
    )
    assert resp_b.status_code == 404
