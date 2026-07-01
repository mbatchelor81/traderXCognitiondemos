def test_account_summary_returns_statistics(client):
    """GET /account/{id}/summary returns aggregated trade statistics."""
    acct = client.post("/account/", json={"displayName": "Summary Test"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # Submit two buy trades and one sell trade
    for security, side, qty in [("AAPL", "Buy", 100), ("MSFT", "Buy", 50), ("AAPL", "Sell", 30)]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": qty,
        })
        assert resp.status_code == 200

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["totalTrades"] == 3
    assert data["settledTrades"] == 3
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 150
    assert data["totalSellQuantity"] == 30
    assert data["netQuantity"] == 120


def test_account_summary_not_found(client):
    """GET /account/{id}/summary returns 404 for missing account."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
