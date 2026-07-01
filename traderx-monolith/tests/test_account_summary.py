"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_statistics(client):
    """Verify summary endpoint returns trade statistics after creating trades."""
    # Arrange - create an account
    acct = client.post("/account/", json={"displayName": "Summary Test Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Create a few trades
    for security, side, qty in [("AAPL", "Buy", 100), ("MSFT", "Buy", 50)]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": qty,
        })
        assert resp.status_code == 200

    # Act
    resp = client.get(f"/account/{account_id}/summary")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 2
    assert data["settledTrades"] >= 0
    assert data["pendingTrades"] >= 0
    assert data["totalBuyQuantity"] >= 0
    assert data["netQuantity"] >= 0


def test_account_summary_empty_account(client):
    """Verify summary returns zeros for an account with no trades."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 0
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_not_found(client):
    """Verify summary returns 404 for a nonexistent account."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
