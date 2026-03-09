"""Smoke tests: exercise the core TraderX workflow end-to-end.

Flow: Create account → Submit trade → Verify trade appears in positions.
This covers cross-service calls (trades-service validates accounts via users-service).
"""

import httpx


def test_create_account_and_trade_flow(users_url, trades_url, http_client):
    """End-to-end: create account, submit trade, verify position created."""

    # Step 1: Create an account via users-service
    account_data = {"displayName": "Smoke Test Account"}
    resp = http_client.post(f"{users_url}/account/", json=account_data)
    assert resp.status_code == 200, f"Failed to create account: {resp.text}"
    account = resp.json()
    account_id = account["id"]
    assert account["displayName"] == "Smoke Test Account"

    # Step 2: Verify account is retrievable
    resp = http_client.get(f"{users_url}/account/{account_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == account_id

    # Step 3: List stocks from trades-service (reference data)
    resp = http_client.get(f"{trades_url}/stocks")
    assert resp.status_code == 200
    stocks = resp.json()
    assert len(stocks) > 0, "No stocks available in reference data"
    ticker = stocks[0]["ticker"]

    # Step 4: Submit a trade via trades-service
    trade_data = {
        "accountId": account_id,
        "security": ticker,
        "side": "Buy",
        "quantity": 100,
    }
    resp = http_client.post(f"{trades_url}/trade/", json=trade_data)
    assert resp.status_code == 200, f"Failed to submit trade: {resp.text}"
    result = resp.json()
    assert result["success"] is True, f"Trade not successful: {result.get('error')}"
    trade = result["trade"]
    assert trade["security"] == ticker
    assert trade["quantity"] == 100
    assert trade["side"] == "Buy"

    # Step 5: Verify trade appears in account trades
    resp = http_client.get(f"{trades_url}/trades/{account_id}")
    assert resp.status_code == 200
    trades_list = resp.json()
    assert len(trades_list) >= 1, "Trade not found in account trades"

    # Step 6: Verify position was created/updated
    resp = http_client.get(f"{trades_url}/positions/{account_id}")
    assert resp.status_code == 200
    positions = resp.json()
    assert len(positions) >= 1, "Position not created after trade"
    # Find the position for our ticker
    pos = next((p for p in positions if p["security"] == ticker), None)
    assert pos is not None, f"No position found for {ticker}"
    assert pos["quantity"] == 100


def test_correlation_id_propagated(users_url, http_client):
    """Verify X-Correlation-ID header is returned in responses."""
    resp = http_client.get(
        f"{users_url}/health",
        headers={"X-Correlation-ID": "smoke-test-correlation-123"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Correlation-ID") == "smoke-test-correlation-123"


def test_tenant_isolation(users_url, http_client):
    """Verify tenant mismatch is rejected."""
    resp = http_client.get(
        f"{users_url}/health",
        headers={"X-Tenant-ID": "wrong_tenant"},
    )
    assert resp.status_code == 403
