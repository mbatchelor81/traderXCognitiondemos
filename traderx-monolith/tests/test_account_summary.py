"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify summary endpoint returns correct trade statistics after trades."""
    # Arrange — create an account and submit trades
    acct = client.post("/account/", json={"displayName": "Summary Test Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit a Buy trade
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert resp.status_code == 200

    # Submit another Buy trade
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Buy",
        "quantity": 50,
    })
    assert resp.status_code == 200

    # Act — fetch the account summary
    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200
    data = summary.json()

    # Assert — structure and values
    assert "account" in data
    assert "statistics" in data
    assert "positions" in data

    stats = data["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 150


def test_account_summary_not_found(client):
    """Verify summary returns 404 for a non-existent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_with_buy_and_sell(client):
    """Verify summary correctly tracks both buy and sell volumes."""
    # Arrange
    acct = client.post("/account/", json={"displayName": "Mixed Trades"})
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
        "quantity": 75,
    })

    # Act
    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200
    stats = summary.json()["statistics"]

    # Assert
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 200
    assert stats["totalSellQuantity"] == 75
    assert stats["netQuantity"] == 125
