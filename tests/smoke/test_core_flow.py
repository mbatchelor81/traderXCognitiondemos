"""Smoke tests — exercise the primary trade lifecycle end-to-end.

This test covers cross-service calls:
  1. Create an account (account-service)
  2. Look up a stock ticker (reference-data-service → validates data exists)
  3. Submit a trade (trading-service → calls account-service + reference-data-service)
  4. Verify trade appears in the blotter (trading-service trades list)
  5. Verify position was created by trading-service (returned in trade response)
"""
import httpx
import pytest


class TestCoreTradeFlow:
    """End-to-end trade lifecycle smoke test."""

    def test_full_trade_lifecycle(self, base_url: str):
        """Create account → validate stock → submit trade → verify trade + position."""
        client = httpx.Client(base_url=base_url, timeout=15.0)

        # Step 1: Create an account
        account_resp = client.post(
            "/account/",
            json={"displayName": "Smoke Test Account"},
        )
        assert account_resp.status_code == 200, f"Create account failed: {account_resp.text}"
        account = account_resp.json()
        account_id = account["id"]
        assert account["displayName"] == "Smoke Test Account"

        # Step 2: Verify a stock ticker exists (cross-service: reference-data)
        stock_resp = client.get("/stocks/AAPL")
        assert stock_resp.status_code == 200, f"Stock lookup failed: {stock_resp.text}"
        stock = stock_resp.json()
        assert stock["ticker"] == "AAPL"

        # Step 3: Submit a trade (cross-service: trading → account + reference-data)
        # Note: trade submission endpoint is POST /trade/ (singular)
        trade_resp = client.post(
            "/trade/",
            json={
                "accountId": account_id,
                "security": "AAPL",
                "side": "Buy",
                "quantity": 100,
            },
        )
        assert trade_resp.status_code == 200, f"Submit trade failed: {trade_resp.text}"
        trade_result = trade_resp.json()
        assert trade_result.get("success") is True, f"Trade not successful: {trade_result}"
        trade = trade_result["trade"]
        assert trade["security"] == "AAPL"
        assert trade["quantity"] == 100
        assert trade["side"] == "Buy"

        # Step 4: Verify trade appears in the blotter (trading-service)
        trades_resp = client.get("/trades/")
        assert trades_resp.status_code == 200
        trades = trades_resp.json()
        trade_ids = [t["id"] for t in trades]
        assert trade["id"] in trade_ids, f"Trade {trade['id']} not found in blotter"

        # Step 5: Verify position was created by trading-service (returned in response)
        # Note: In the single-tenant architecture, trading-service manages both trades
        # and positions in its own database. The position-service has a separate database
        # for read-only queries. The trade response includes the position data.
        position = trade_result["position"]
        assert position is not None, "Trade response should include position data"
        assert position["accountId"] == account_id
        assert position["security"] == "AAPL"
        assert position["quantity"] == 100

        client.close()

    def test_account_list_returns_json(self, base_url: str):
        """Account list endpoint should return a JSON array."""
        resp = httpx.get(f"{base_url}/account/", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_positions_list_returns_json(self, base_url: str):
        """Positions list endpoint should return a JSON array."""
        resp = httpx.get(f"{base_url}/positions/", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
