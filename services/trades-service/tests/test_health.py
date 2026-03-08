"""Tests for /health endpoint."""


def test_health_endpoint(client):
    """Test that /health returns correct response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "trades-service"
    assert data["tenant"] == "acme_corp"
