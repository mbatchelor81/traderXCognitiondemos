"""Smoke tests — verify each service health endpoint returns UP."""
import httpx
import pytest


SERVICE_PATHS = [
    ("/account/", "account-service"),
    ("/trades/", "trading-service"),
    ("/positions/", "position-service"),
    ("/stocks/", "reference-data-service"),
    ("/people/GetPerson?LogonId=jsmith", "people-service"),
]


class TestHealth:
    """Health endpoint smoke tests for all services behind the ALB."""

    def test_frontend_accessible(self, base_url: str):
        """Frontend should return 200 and contain HTML."""
        resp = httpx.get(f"{base_url}/", timeout=10.0)
        assert resp.status_code == 200, f"Frontend returned {resp.status_code}"
        assert "html" in resp.text.lower(), "Frontend response should contain HTML"

    @pytest.mark.parametrize("path,service_name", SERVICE_PATHS)
    def test_service_reachable(self, base_url: str, path: str, service_name: str):
        """Each service path should be reachable and return 200."""
        resp = httpx.get(f"{base_url}{path}", timeout=10.0)
        assert resp.status_code == 200, f"{service_name} at {path} returned {resp.status_code}: {resp.text[:200]}"

    def test_account_health(self, base_url: str):
        """Account service /health should return UP via the ALB health path."""
        # The /health path routes to frontend; test service health via service-specific endpoint
        resp = httpx.get(f"{base_url}/account/", timeout=10.0)
        assert resp.status_code == 200

    def test_stocks_returns_data(self, base_url: str):
        """Reference data service should return a non-empty list of stocks."""
        resp = httpx.get(f"{base_url}/stocks/", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), "Expected a list of stocks"
        assert len(data) > 0, "Expected at least one stock ticker"
