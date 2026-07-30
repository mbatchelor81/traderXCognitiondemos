"""Health, root, tenancy and observability behaviour."""

from tests.conftest import TENANT_ID


def test_health_returns_exact_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "UP",
        "service": "reference-data-service",
        "tenant": TENANT_ID,
    }


def test_root_reports_service_metadata(client):
    body = client.get("/").json()
    assert body["service"] == "reference-data-service"
    assert body["tenant"] == TENANT_ID


def test_matching_tenant_header_is_allowed(client):
    response = client.get("/health", headers={"X-Tenant-ID": TENANT_ID})
    assert response.status_code == 200


def test_mismatched_tenant_header_is_rejected(client):
    response = client.get("/health", headers={"X-Tenant-ID": "other_tenant"})
    assert response.status_code == 403
    assert "other_tenant" in response.json()["detail"]


def test_mismatched_tenant_header_is_rejected_on_stocks(client):
    response = client.get("/stocks/", headers={"X-Tenant-ID": "other_tenant"})
    assert response.status_code == 403


def test_correlation_id_is_echoed_when_supplied(client):
    response = client.get("/health", headers={"X-Correlation-ID": "abc-123"})
    assert response.headers["X-Correlation-ID"] == "abc-123"


def test_correlation_id_is_generated_when_absent(client):
    response = client.get("/health")
    assert response.headers.get("X-Correlation-ID")


def test_openapi_spec_is_served(client):
    spec = client.get("/openapi.json").json()
    assert "/stocks/" in spec["paths"]
    assert "/stocks/{ticker}" in spec["paths"]
