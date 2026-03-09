"""Test /health endpoint for users-service."""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "users-service"
    assert data["tenant"] == "acme_corp"
