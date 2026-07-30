"""Health, metrics and frontend availability through the gateway."""

import pytest

from conftest import SERVICES


@pytest.mark.parametrize("service,slug", SERVICES)
def test_service_health(client, tenant_id, service, slug):
    """`/health` is ambiguous behind a shared hostname, so each service also
    answers on its own `/svc/<slug>/health` alias."""
    response = client.get(f"/svc/{slug}/health")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "UP",
        "service": service,
        "tenant": tenant_id,
    }


@pytest.mark.parametrize("service,slug", SERVICES)
def test_service_metrics(client, service, slug):
    response = client.get(f"/svc/{slug}/metrics")

    assert response.status_code == 200, response.text
    assert "http_requests_total" in response.text
    assert f'service="{service}"' in response.text


@pytest.mark.parametrize("service,slug", SERVICES)
def test_mismatched_tenant_is_rejected(client, service, slug):
    response = client.get(
        f"/svc/{slug}/health", headers={"X-Tenant-ID": "some_other_tenant"}
    )

    assert response.status_code == 403, f"{service} accepted a foreign tenant header"


def test_frontend_is_served(client):
    response = client.get("/")

    assert response.status_code == 200, response.text
    assert '<div id="root">' in response.text


def test_frontend_spa_fallback(client):
    """Deep links must return the SPA shell rather than a 404."""
    response = client.get("/some/client-side/route")

    assert response.status_code == 200
    assert '<div id="root">' in response.text
