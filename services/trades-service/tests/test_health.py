"""Test /health endpoint for trades-service."""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "trades-service"
    assert data["tenant"] == "acme_corp"
