"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify the summary endpoint returns aggregated trade statistics."""
    # Arrange — create an account and submit some trades
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

    # Act — fetch the summary
    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200

    body = summary.json()

    # Assert — structure
    assert "account" in body
    assert "statistics" in body
    assert "positions" in body

    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 150


def test_account_summary_not_found(client):
    """Verify the summary endpoint returns 404 for a non-existent account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_account_summary_with_mixed_sides(client):
    """Verify buy and sell quantities are computed correctly."""
    acct = client.post("/account/", json={"displayName": "Mixed Trades"})
    account_id = acct.json()["id"]

    # Buy 200 shares
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "GOOG",
        "side": "Buy",
        "quantity": 200,
    })

    # Sell 75 shares
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "GOOG",
        "side": "Sell",
        "quantity": 75,
    })

    summary = client.get(f"/account/{account_id}/summary")
    assert summary.status_code == 200

    stats = summary.json()["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 200
    assert stats["totalSellQuantity"] == 75
    assert stats["netQuantity"] == 125
