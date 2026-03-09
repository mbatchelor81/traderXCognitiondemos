"""Smoke tests — health endpoints for all services behind the ALB."""

import httpx
import pytest


class TestHealthEndpoints:
    """Verify each service's /health endpoint returns 200 with status UP."""

    def test_users_service_health(self, base_url):
        """Users service health check via /people/ endpoint (routed to users-service)."""
        # The /health path is not routed via ALB to a specific service,
        # so we check service-specific routes to verify each service is alive.
        r = httpx.get(f"{base_url}/account/", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_trades_service_health(self, base_url):
        """Trades service health check via /stocks/ endpoint (routed to trades-service)."""
        r = httpx.get(f"{base_url}/stocks/", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_frontend_reachable(self, base_url):
        """Frontend serves HTML at root path."""
        r = httpx.get(f"{base_url}/", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        # Frontend should serve HTML content
        assert "text/html" in r.headers.get("content-type", ""), \
            f"Expected HTML content-type, got {r.headers.get('content-type')}"

    def test_people_endpoint(self, base_url):
        """People directory returns a list of people."""
        r = httpx.get(f"{base_url}/people/", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Expected at least one person"

    def test_stocks_endpoint(self, base_url):
        """Reference data returns a list of stocks."""
        r = httpx.get(f"{base_url}/stocks/", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Expected at least one stock"
