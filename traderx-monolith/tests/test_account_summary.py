"""Integration tests for the GET /account/{account_id}/summary endpoint."""


TENANT = "acme_corp"
HEADERS = {"X-Tenant-ID": TENANT}


def _create_account(client, name="Test Account"):
    resp = client.post("/account/", json={"displayName": name}, headers=HEADERS)
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100):
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    }, headers=HEADERS)
    assert resp.status_code == 200
    return resp.json()


def test_summary_returns_zeros_for_empty_account(client):
    """An account with no trades should return all-zero statistics."""
    account_id = _create_account(client)
    resp = client.get(f"/account/{account_id}/summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_summary_reflects_submitted_trades(client):
    """Statistics should reflect trades that have been submitted."""
    account_id = _create_account(client)
    _submit_trade(client, account_id, "AAPL", "Buy", 100)
    _submit_trade(client, account_id, "MSFT", "Buy", 50)

    resp = client.get(f"/account/{account_id}/summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    # Trades settle immediately in the monolith, so both should be settled
    assert data["settledTrades"] == 2
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 150


def test_summary_buy_and_sell(client):
    """Net quantity should reflect buys minus sells."""
    account_id = _create_account(client)
    _submit_trade(client, account_id, "AAPL", "Buy", 200)
    _submit_trade(client, account_id, "AAPL", "Sell", 75)

    resp = client.get(f"/account/{account_id}/summary", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["totalBuyQuantity"] == 200
    assert data["totalSellQuantity"] == 75
    assert data["netQuantity"] == 125


def test_summary_404_for_nonexistent_account(client):
    """Should return 404 for an account that doesn't exist."""
    resp = client.get("/account/99999/summary", headers=HEADERS)
    assert resp.status_code == 404
