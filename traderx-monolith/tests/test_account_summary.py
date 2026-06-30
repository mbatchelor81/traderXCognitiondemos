"""Tests for account summary statistics."""


def test_get_account_summary(client):
    create_resp = client.post("/account/", json={"displayName": "Summary Account"})
    assert create_resp.status_code == 200
    account_id = create_resp.json()["id"]

    first_trade = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert first_trade.status_code == 200

    second_trade = client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Sell",
        "quantity": 40,
    })
    assert second_trade.status_code == 200

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["accountId"] == account_id
    assert data["totalTrades"] == 2
    assert data["settledTrades"] == 2
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 100
    assert data["totalSellQuantity"] == 40
    assert data["netQuantity"] == 60


def test_get_account_summary_not_found(client):
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Account 999999 not found"
