"""Health, tenancy and OpenAPI tests."""
from unittest.mock import patch

from tests.conftest import TEST_TENANT_ID


def test_health_returns_exact_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "UP",
        "service": "position-service",
        "tenant": TEST_TENANT_ID,
    }


def test_health_reports_down_when_database_unreachable(client):
    with patch("app.main.text", side_effect=RuntimeError("db gone")):
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {
        "status": "DOWN",
        "service": "position-service",
        "tenant": TEST_TENANT_ID,
    }


def test_matching_tenant_header_is_allowed(client):
    response = client.get("/health", headers={"X-Tenant-ID": TEST_TENANT_ID})
    assert response.status_code == 200


def test_mismatched_tenant_header_is_rejected(client):
    response = client.get("/health", headers={"X-Tenant-ID": "other_tenant"})
    assert response.status_code == 403
    assert "other_tenant" in response.json()["detail"]


def test_mismatched_tenant_header_rejected_on_writes(client):
    response = client.post(
        "/positions/apply",
        json={"accountId": 1, "security": "AAPL", "quantityDelta": 10},
        headers={"X-Tenant-ID": "other_tenant"},
    )
    assert response.status_code == 403


def test_correlation_id_is_echoed(client):
    response = client.get("/health", headers={"X-Correlation-ID": "corr-123"})
    assert response.headers["X-Correlation-ID"] == "corr-123"


def test_correlation_id_is_generated_when_absent(client):
    response = client.get("/health")
    assert response.headers.get("X-Correlation-ID")


def test_openapi_spec_is_served(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/positions/" in paths
    assert "/positions/apply" in paths
    assert "/positions/recalculate" in paths


def test_root_reports_tenant(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["tenant"] == TEST_TENANT_ID
    assert response.json()["service"] == "position-service"
