"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify the summary endpoint returns aggregated trade statistics."""
    # Arrange — create an account and a couple of trades
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
        "side": "Sell",
        "quantity": 40,
    })

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] >= 0
    assert stats["pendingTrades"] >= 0
    assert stats["totalBuyQuantity"] == 100
    assert stats["totalSellQuantity"] == 40
    assert stats["netQuantity"] == 60


def test_account_summary_not_found(client):
    """Verify 404 when account does not exist."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
