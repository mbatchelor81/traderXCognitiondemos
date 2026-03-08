"""Smoke tests: verify each service's /health endpoint via the ALB."""

import httpx
import pytest


def test_users_service_health(base_url: str):
    """Users service /health should return 200 with status UP."""
    response = httpx.get(f"{base_url}/health", timeout=10.0)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "UP", f"Expected status UP, got {data}"
    assert "service" in data, "Missing 'service' field in health response"
    assert "tenant" in data, "Missing 'tenant' field in health response"


def test_trades_service_reachable(base_url: str):
    """Trades service should be reachable via ALB path-based routing."""
    # /positions/ is routed to trades-service by the ALB
    response = httpx.get(f"{base_url}/positions/", timeout=10.0)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_trades_service_reference_data(base_url: str):
    """Trades service /stocks/ should return stock data."""
    response = httpx.get(f"{base_url}/stocks/", timeout=10.0)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list), f"Expected list of stocks, got {type(data)}"
    assert len(data) > 0, "Expected at least one stock in reference data"
