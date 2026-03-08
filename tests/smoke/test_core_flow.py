"""Smoke tests: exercise the primary workflow end-to-end through the ALB.

This covers a cross-service call path:
  1. Create an account via users-service (ALB default route)
  2. List reference data via trades-service (ALB /reference-data* route)
  3. Submit a trade via trades-service (ALB /trade* route) — this triggers
     a cross-service call from trades-service to users-service for account validation
  4. Verify the trade appears in the trades list
"""

import httpx
import pytest


def test_create_account(base_url: str):
    """Create an account via the users-service through ALB."""
    payload = {"displayName": "Smoke Test Account"}
    response = httpx.post(f"{base_url}/account/", json=payload, timeout=10.0)
    assert response.status_code == 200, f"Failed to create account: {response.status_code} {response.text}"
    data = response.json()
    assert "id" in data, f"Account response missing 'id': {data}"
    assert data["displayName"] == "Smoke Test Account", f"Unexpected displayName: {data}"


def test_list_accounts(base_url: str):
    """List accounts via users-service through ALB."""
    response = httpx.get(f"{base_url}/account/", timeout=10.0)
    assert response.status_code == 200, f"Failed to list accounts: {response.status_code} {response.text}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"


def test_reference_data_stocks(base_url: str):
    """Get stock reference data via trades-service through ALB."""
    response = httpx.get(f"{base_url}/stocks/", timeout=10.0)
    assert response.status_code == 200, f"Failed to get stocks: {response.status_code} {response.text}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) > 0, "Expected at least one stock"
    # Verify stock structure
    stock = data[0]
    assert "ticker" in stock, f"Stock missing 'ticker': {stock}"
    assert "companyName" in stock, f"Stock missing 'companyName': {stock}"


def test_cross_service_trade_flow(base_url: str):
    """End-to-end: create account, submit trade, verify trade exists.

    This exercises a cross-service call: trades-service validates the
    account via users-service before processing the trade.
    """
    # Step 1: Create an account
    account_resp = httpx.post(
        f"{base_url}/account/",
        json={"displayName": "E2E Smoke Test Account"},
        timeout=10.0,
    )
    assert account_resp.status_code == 200, f"Account creation failed: {account_resp.text}"
    account_id = account_resp.json()["id"]

    # Step 2: Get a valid stock ticker from reference data
    stocks_resp = httpx.get(f"{base_url}/stocks/", timeout=10.0)
    assert stocks_resp.status_code == 200, f"Reference data failed: {stocks_resp.text}"
    stocks = stocks_resp.json()
    assert len(stocks) > 0, "No stocks available"
    ticker = stocks[0]["ticker"]

    # Step 3: Submit a trade (cross-service call: trades -> users for account validation)
    trade_resp = httpx.post(
        f"{base_url}/trade/",
        json={
            "accountId": account_id,
            "security": ticker,
            "side": "Buy",
            "quantity": 100,
        },
        timeout=15.0,
    )
    assert trade_resp.status_code == 200, f"Trade submission failed: {trade_resp.text}"
    trade_data = trade_resp.json()
    assert trade_data.get("success") is True, f"Trade not successful: {trade_data}"

    # Step 4: Verify trade appears in the trades list
    trades_resp = httpx.get(f"{base_url}/trades/", timeout=10.0)
    assert trades_resp.status_code == 200, f"List trades failed: {trades_resp.text}"
    trades = trades_resp.json()
    assert isinstance(trades, list), f"Expected list, got {type(trades)}"
    # At least the trade we just created should be in the list
    assert len(trades) > 0, "Expected at least one trade after submission"


def test_positions_after_trade(base_url: str):
    """Verify positions endpoint returns data (positions are updated after trades)."""
    response = httpx.get(f"{base_url}/positions/", timeout=10.0)
    assert response.status_code == 200, f"Failed to get positions: {response.status_code} {response.text}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
