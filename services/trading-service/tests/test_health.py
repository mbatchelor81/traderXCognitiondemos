"""Health, tenancy and OpenAPI tests."""

from unittest.mock import MagicMock

from app.config import SERVICE_NAME, TENANT_ID
from app.database import get_db
from app.main import app


def test_health_returns_exact_contract(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "UP",
        "service": SERVICE_NAME,
        "tenant": TENANT_ID,
    }


def test_health_returns_503_when_database_is_down(client):
    broken_db = MagicMock()
    broken_db.execute.side_effect = RuntimeError("connection refused")
    app.dependency_overrides[get_db] = lambda: broken_db

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "DOWN",
        "service": SERVICE_NAME,
        "tenant": TENANT_ID,
    }


def test_matching_tenant_header_is_accepted(client):
    response = client.get("/health", headers={"X-Tenant-ID": TENANT_ID})

    assert response.status_code == 200


def test_mismatched_tenant_header_is_rejected(client):
    response = client.get("/health", headers={"X-Tenant-ID": "other_tenant"})

    assert response.status_code == 403
    assert "other_tenant" in response.json()["detail"]


def test_correlation_id_is_echoed(client):
    response = client.get("/health", headers={"X-Correlation-ID": "corr-123"})

    assert response.headers["X-Correlation-ID"] == "corr-123"


def test_correlation_id_is_generated_when_absent(client):
    response = client.get("/health")

    assert response.headers.get("X-Correlation-ID")


def test_openapi_spec_documents_the_trade_endpoints(client):
    spec = client.get("/openapi.json").json()

    assert "/trade/" in spec["paths"]
    assert "/trades/" in spec["paths"]
    assert "/analytics/trades" in spec["paths"]
    assert spec["paths"]["/trade/"]["post"]["summary"] == "Submit a trade order"
