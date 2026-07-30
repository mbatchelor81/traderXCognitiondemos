"""Health, tenancy and OpenAPI tests."""

from tests.conftest import TEST_TENANT_ID


def test_health_returns_exact_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "UP",
        "service": "account-service",
        "tenant": TEST_TENANT_ID,
    }


def test_health_accepts_matching_tenant_header(client):
    resp = client.get("/health", headers={"X-Tenant-ID": TEST_TENANT_ID})
    assert resp.status_code == 200


def test_mismatched_tenant_header_is_rejected(client):
    resp = client.get("/health", headers={"X-Tenant-ID": "other_tenant"})
    assert resp.status_code == 403
    assert "other_tenant" in resp.json()["detail"]


def test_mismatched_tenant_header_rejected_on_account_routes(client):
    resp = client.get("/account/", headers={"X-Tenant-ID": "other_tenant"})
    assert resp.status_code == 403


def test_correlation_id_is_echoed(client):
    resp = client.get("/health", headers={"X-Correlation-ID": "corr-123"})
    assert resp.headers["X-Correlation-ID"] == "corr-123"


def test_correlation_id_is_generated_when_absent(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Correlation-ID")


def test_openapi_is_available(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    for path in (
        "/account/",
        "/account/{account_id}",
        "/account/{account_id}/exists",
        "/accountuser/",
        "/health",
    ):
        assert path in paths
