"""Health, root and OpenAPI tests."""

from tests.conftest import TEST_TENANT


def test_health_returns_exact_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "UP",
        "service": "people-service",
        "tenant": TEST_TENANT,
    }


def test_root_reports_service_identity(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "service": "people-service",
        "version": "1.0.0",
        "status": "running",
        "tenant": TEST_TENANT,
    }


def test_openapi_spec_documents_people_routes(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/people/GetPerson" in paths
    assert "/people/GetMatchingPeople" in paths
    assert "/people/ValidatePerson" in paths
    assert paths["/people/ValidatePerson"]["get"]["summary"] == "Validate that a person exists"
