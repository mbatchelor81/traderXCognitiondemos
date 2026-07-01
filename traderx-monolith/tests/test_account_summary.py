"""Tests for the GET /account/{account_id}/summary endpoint."""


def test_summary_returns_statistics(client):
    """Create an account, submit trades, and verify the summary endpoint."""
    # Create an account
    resp = client.post("/account/", json={"displayName": "Summary Test"})
    assert resp.status_code == 200
    account_id = resp.json()["id"]

    # Submit a Buy trade
    resp = client.post(
        "/trade/",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
    )
    assert resp.status_code == 200

    # Submit another Buy trade
    resp = client.post(
        "/trade/",
        json={
            "accountId": account_id,
            "security": "MSFT",
            "side": "Buy",
            "quantity": 50,
        },
    )
    assert resp.status_code == 200

    # Get the summary
    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    # Verify structure
    assert "account" in data
    assert "statistics" in data
    stats = data["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["totalBuyQuantity"] == 150
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 150


def test_summary_not_found(client):
    """Summary for a non-existent account returns 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
