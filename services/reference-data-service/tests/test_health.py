"""Test /health endpoint for Reference Data Service."""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "reference-data-service"
    assert data["tenant"] == "test_tenant"
