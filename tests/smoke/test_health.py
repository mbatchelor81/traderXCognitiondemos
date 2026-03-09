"""Smoke tests: verify each service's /health endpoint returns UP."""

import httpx


def test_users_service_health(users_url, http_client):
    """Users service /health should return 200 with status UP."""
    resp = http_client.get(f"{users_url}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert data["service"] == "users-service"


def test_trades_service_health(trades_url, http_client):
    """Trades service /health should return 200 with status UP."""
    resp = http_client.get(f"{trades_url}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert data["service"] == "trades-service"


def test_frontend_health(frontend_url, http_client):
    """Frontend /health should return 200 with status UP."""
    resp = http_client.get(f"{frontend_url}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert data["service"] == "frontend"


def test_users_service_metrics(users_url, http_client):
    """Users service /metrics should return Prometheus metrics."""
    resp = http_client.get(f"{users_url}/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text


def test_trades_service_metrics(trades_url, http_client):
    """Trades service /metrics should return Prometheus metrics."""
    resp = http_client.get(f"{trades_url}/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
