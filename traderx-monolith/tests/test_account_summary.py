"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint returns trade statistics after creating trades."""
    # Arrange — create an account and submit trades
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "MSFT",
        "side": "Buy", "quantity": 50,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Sell", "quantity": 30,
    })

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    stats = body["statistics"]
    assert stats["totalTrades"] == 3
    assert stats["settledTrades"] >= 0
    assert stats["pendingTrades"] >= 0
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 30
    assert stats["netQuantity"] == 120


def test_account_summary_not_found(client):
    """Summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_empty_account(client):
    """Summary endpoint returns zero statistics for an account with no trades."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0
