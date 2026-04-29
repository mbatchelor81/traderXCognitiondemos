"""Tests for the GET /account/{account_id}/summary endpoint."""


def _create_account(client, name="Test Account"):
    resp = client.post("/account/", json={"displayName": name})
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100):
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    return resp.json()


def test_summary_returns_zeros_for_empty_account(client):
    account_id = _create_account(client)
    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_summary_reflects_submitted_trades(client):
    account_id = _create_account(client)
    _submit_trade(client, account_id, "AAPL", "Buy", 100)
    _submit_trade(client, account_id, "MSFT", "Sell", 50)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["settledTrades"] + data["pendingTrades"] == data["totalTrades"]


def test_summary_returns_404_for_missing_account(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
