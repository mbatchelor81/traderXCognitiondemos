"""Tests for GET /account/{account_id}/summary endpoint."""


def test_account_summary_returns_zero_stats_for_new_account(client):
    """A freshly created account should have all-zero trade statistics."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["accountId"] == account_id
    stats = body["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["totalBuyQuantity"] == 0
    assert stats["totalSellQuantity"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_reflects_submitted_trades(client):
    """After submitting trades, the summary should count them."""
    acct = client.post("/account/", json={"displayName": "Active Account"})
    account_id = acct.json()["id"]

    for security, quantity in [("AAPL", 100), ("MSFT", 50)]:
        r = client.post(
            "/trade/",
            json={
                "accountId": account_id,
                "security": security,
                "side": "Buy",
                "quantity": quantity,
            },
        )
        assert r.status_code == 200

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 2


def test_account_summary_unknown_account_returns_404(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
