"""Tests for the account summary endpoint."""


def test_get_account_summary_returns_statistics(client):
    """Test that the summary endpoint returns trade statistics for an account."""
    # Arrange — create an account and submit trades
    resp = client.post("/account/", json={"displayName": "Summary Test"})
    assert resp.status_code == 200
    account_id = resp.json()["id"]

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

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["settledTrades"] == 2
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 150


def test_get_account_summary_not_found(client):
    """Test that the summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
