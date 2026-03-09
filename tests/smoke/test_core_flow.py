"""Smoke tests — core trade flow exercising cross-service calls."""

import httpx
import pytest


class TestCoreTradeFlow:
    """Exercise the primary trade workflow end-to-end through the ALB.

    Flow: list accounts (users-service) → list stocks (trades-service)
          → submit trade (trades-service, which calls users-service for validation)
          → verify trade appears in blotter
    """

    def test_list_accounts(self, base_url):
        """Verify accounts can be listed from users-service."""
        r = httpx.get(f"{base_url}/account/", timeout=10)
        assert r.status_code == 200
        accounts = r.json()
        assert isinstance(accounts, list), f"Expected list, got {type(accounts)}"
        assert len(accounts) > 0, "Expected at least one account"
        # Store first account ID for later tests
        account = accounts[0]
        assert "id" in account, f"Account missing 'id' field: {account}"

    def test_list_stocks(self, base_url):
        """Verify stocks can be listed from trades-service."""
        r = httpx.get(f"{base_url}/stocks/", timeout=10)
        assert r.status_code == 200
        stocks = r.json()
        assert isinstance(stocks, list)
        assert len(stocks) > 0, "Expected at least one stock"
        stock = stocks[0]
        assert "Ticker" in stock or "ticker" in stock, \
            f"Stock missing ticker field: {stock}"

    def test_submit_trade_cross_service(self, base_url):
        """Submit a trade — exercises cross-service call (trades → users for account validation)."""
        # Step 1: Get a valid account ID
        accounts_resp = httpx.get(f"{base_url}/account/", timeout=10)
        assert accounts_resp.status_code == 200
        accounts = accounts_resp.json()
        assert len(accounts) > 0, "No accounts available"
        account_id = accounts[0]["id"]

        # Step 2: Get a valid stock ticker
        stocks_resp = httpx.get(f"{base_url}/stocks/", timeout=10)
        assert stocks_resp.status_code == 200
        stocks = stocks_resp.json()
        assert len(stocks) > 0, "No stocks available"
        ticker = stocks[0].get("Ticker") or stocks[0].get("ticker")

        # Step 3: Submit a trade (POST /trade/)
        trade_payload = {
            "accountId": account_id,
            "security": ticker,
            "side": "Buy",
            "quantity": 10,
        }
        trade_resp = httpx.post(
            f"{base_url}/trade/",
            json=trade_payload,
            timeout=15,
        )
        # Accept 200 or 201 for successful trade submission
        assert trade_resp.status_code in (200, 201), \
            f"Trade submission failed with {trade_resp.status_code}: {trade_resp.text}"
        trade_data = trade_resp.json()
        # Response may wrap trade in a 'trade' key with 'success' flag
        if "success" in trade_data:
            assert trade_data["success"] is True, f"Trade not successful: {trade_data}"
            trade_obj = trade_data.get("trade", {})
            assert "id" in trade_obj and "state" in trade_obj, \
                f"Trade object missing expected fields: {trade_obj}"
        else:
            assert "id" in trade_data or "state" in trade_data, \
                f"Trade response missing expected fields: {trade_data}"

    def test_positions_endpoint(self, base_url):
        """Verify positions endpoint is reachable."""
        r = httpx.get(f"{base_url}/positions/", timeout=10)
        # Positions may return empty list if no trades have been processed yet
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"

    def test_trades_endpoint(self, base_url):
        """Verify trades list endpoint is reachable."""
        r = httpx.get(f"{base_url}/trades/", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
