"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_get_account_summary_returns_statistics(client):
    """Verify the summary endpoint returns aggregated trade statistics."""
    # Arrange — create an account and submit a few trades
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
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
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 30,
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


def test_get_account_summary_not_found(client):
    """Verify 404 when account does not exist."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_get_account_summary_empty_account(client):
    """Verify summary for an account with no trades."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0
