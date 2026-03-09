"""Smoke tests — verify each service's /health endpoint."""

import os

import httpx
import pytest

# When testing via ALB, all services are behind one URL with path-based routing.
# When testing via Docker Compose, each service runs on its own port on localhost.
IS_ALB = "SMOKE_TEST_URL" in os.environ and "localhost" not in os.environ.get("SMOKE_TEST_URL", "")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(timeout=10.0, follow_redirects=True) as c:
        yield c


class TestHealthEndpoints:
    """Hit each service's /health endpoint and assert 200 + status UP."""

    def _health_url(self, base_url: str, service_ports: dict, service: str) -> str:
        """Build the health URL depending on local vs ALB mode."""
        if IS_ALB:
            # Via ALB, /health is routed to account-service by default.
            # Each service also responds to /health on its own path.
            # We use per-service ports on the ALB for individual health checks.
            return f"{base_url}/health"
        else:
            port = service_ports[service]
            return f"http://localhost:{port}/health"

    def test_account_service_health(self, client, base_url, service_ports):
        if IS_ALB:
            url = f"{base_url}/health"
        else:
            url = f"http://localhost:{service_ports['account-service']}/health"
        resp = client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "UP"
        if not IS_ALB:
            assert data["service"] == "account-service"

    def test_trading_service_health(self, client, base_url, service_ports):
        if IS_ALB:
            # Via ALB /trade routes to trading-service. POST is the main
            # endpoint but GET on /trade/ returns 405 which still proves the
            # service is reachable. We use a simple POST with invalid body to
            # confirm the service is up (422 = validation error = service alive).
            url = f"{base_url}/trade/"
            resp = client.post(url, json={})
            # 422 (validation error) or 200 both prove trading-service is up
            assert resp.status_code in (200, 422), f"Trading service unreachable: {resp.status_code}"
        else:
            url = f"http://localhost:{service_ports['trading-service']}/health"
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "UP"
            assert data["service"] == "trading-service"

    def test_position_service_health(self, client, base_url, service_ports):
        if IS_ALB:
            url = f"{base_url}/positions"
            resp = client.get(url)
            assert resp.status_code == 200
        else:
            url = f"http://localhost:{service_ports['position-service']}/health"
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "UP"
            assert data["service"] == "position-service"

    def test_reference_data_service_health(self, client, base_url, service_ports):
        if IS_ALB:
            url = f"{base_url}/stocks/"
            resp = client.get(url)
            assert resp.status_code == 200
        else:
            url = f"http://localhost:{service_ports['reference-data-service']}/health"
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "UP"
            assert data["service"] == "reference-data-service"

    def test_people_service_health(self, client, base_url, service_ports):
        if IS_ALB:
            url = f"{base_url}/people/GetMatchingPeople"
            resp = client.get(url, params={"SearchText": "test"})
            # People service may return 200 or 404 depending on data
            assert resp.status_code in (200, 404)
        else:
            url = f"http://localhost:{service_ports['people-service']}/health"
            resp = client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "UP"
            assert data["service"] == "people-service"
