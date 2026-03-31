"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify the summary endpoint returns aggregated trade statistics."""
    # Arrange — create account and submit trades
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

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] == 2
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 150
    assert body["account"]["id"] == account_id
    assert len(body["positions"]) == 2


def test_account_summary_with_buy_and_sell(client):
    """Verify buy and sell quantities are tracked separately."""
    acct = client.post("/account/", json={"displayName": "Buy Sell Test"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Buy", "quantity": 200,
    })
    client.post("/trade/", json={
        "accountId": account_id, "security": "AAPL",
        "side": "Sell", "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 200
    assert stats["totalSellQuantity"] == 50
    assert stats["netQuantity"] == 150


def test_account_summary_not_found(client):
    """Verify 404 is returned for a non-existent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_account_summary_no_trades(client):
    """Verify summary returns zero stats when no trades exist."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0
