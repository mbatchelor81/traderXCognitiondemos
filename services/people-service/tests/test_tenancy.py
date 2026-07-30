"""Single-tenant enforcement tests."""

import pytest

from tests.conftest import TEST_TENANT


@pytest.mark.parametrize(
    "path",
    ["/health", "/people/GetPerson?LogonId=jsmith", "/people/ValidatePerson?LogonId=jsmith"],
)
def test_mismatched_tenant_header_is_rejected(client, path):
    response = client.get(path, headers={"X-Tenant-ID": "other_tenant"})
    assert response.status_code == 403
    assert "other_tenant" in response.json()["detail"]


def test_matching_tenant_header_is_accepted(client):
    response = client.get("/health", headers={"X-Tenant-ID": TEST_TENANT})
    assert response.status_code == 200
    assert response.json()["tenant"] == TEST_TENANT


def test_missing_tenant_header_uses_startup_tenant(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["tenant"] == TEST_TENANT
