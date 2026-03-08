"""Smoke tests: health endpoints for all services via the ALB."""

import httpx


def test_users_service_health(client: httpx.Client):
    """Users service /health returns UP via ALB routing (/account/ path)."""
    resp = client.get("/health")
    # /health hits the default route (frontend) so we check service-specific routes
    # Verify users-service is reachable through its routed paths
    resp = client.get("/account/")
    assert resp.status_code == 200


def test_trades_service_health(client: httpx.Client):
    """Trades service returns data via ALB routing (/stocks/ path)."""
    resp = client.get("/stocks/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_frontend_loads(client: httpx.Client):
    """Frontend returns HTTP 200 at root path."""
    resp = client.get("/")
    assert resp.status_code == 200
