"""Trade analytics endpoint tests."""

from tests.conftest import TEST_ACCOUNT_ID


def test_tenant_trade_analytics(client, seeded_trades):
    response = client.get("/analytics/trades")

    assert response.status_code == 200
    stats = response.json()
    assert stats["totalTrades"] == 3
    assert stats["buyCount"] == 2
    assert stats["sellCount"] == 1
    assert stats["buySellRatio"] == 2.0
    assert stats["tradesByState"] == {"Settled": 2, "Processing": 1}
    assert stats["tradesBySecurity"]["AAPL"] == 2
    assert stats["recentActivity"]["last7Days"] == 3


def test_tenant_trade_analytics_with_no_trades(client):
    response = client.get("/analytics/trades")

    assert response.status_code == 200
    assert response.json()["totalTrades"] == 0
    assert response.json()["tradesByState"] == {}


def test_account_trade_analytics(client, seeded_trades):
    response = client.get(f"/analytics/trades/{TEST_ACCOUNT_ID}")

    assert response.status_code == 200
    stats = response.json()
    assert stats["accountId"] == TEST_ACCOUNT_ID
    assert stats["totalTrades"] == 2
    assert stats["averageQuantity"] == 70.0
    assert stats["tradesBySecurity"] == {"AAPL": 2}


def test_account_trade_analytics_for_unknown_account_is_empty(client, seeded_trades):
    response = client.get("/analytics/trades/99999")

    assert response.status_code == 200
    assert response.json()["totalTrades"] == 0


def test_account_trade_analytics_rejects_non_numeric_account(client):
    response = client.get("/analytics/trades/not-a-number")

    assert response.status_code == 422
