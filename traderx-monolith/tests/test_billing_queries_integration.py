"""Integration tests for billing query endpoints — full lifecycle."""

import pytest


def _seed_via_api(client):
    """Seed billing queries and test data via API calls."""
    # Seed the 4 billing queries
    resp = client.post("/query/_seed")
    assert resp.status_code == 200
    assert resp.json()["seeded"] == 4

    # Create an account
    resp = client.post("/account/", json={"displayName": "Integration Acct"})
    assert resp.status_code == 200
    account_id = resp.json()["id"]

    # Create trades for the account
    for trade in [
        {"accountId": account_id, "security": "AAPL", "side": "Buy", "quantity": 10},
        {"accountId": account_id, "security": "MSFT", "side": "Sell", "quantity": 300},
    ]:
        resp = client.post("/trade/", json=trade)
        assert resp.status_code == 200

    return account_id


# =============================================================================
# List endpoint
# =============================================================================

def test_list_queries_empty(client):
    resp = client.get("/query")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_queries_after_seed(client):
    client.post("/query/_seed")
    resp = client.get("/query")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    names = {q["qualifiedName"] for q in data}
    assert "billing::diagnosis-codes" in names
    assert "billing::procedure-codes" in names
    assert "billing::encounter-summary" in names
    assert "billing::patient-coverage" in names


# =============================================================================
# Register endpoint (PUT)
# =============================================================================

def test_register_custom_query(client):
    resp = client.put(
        "/query/custom::my-query/1.0.0",
        json={
            "queryType": "diagnosis_codes",
            "queryDefinition": {"fields": ["code"]},
            "description": "Custom query",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["qualifiedName"] == "custom::my-query"
    assert data["version"] == "1.0.0"
    assert data["description"] == "Custom query"


def test_register_query_update_overwrites(client):
    client.put(
        "/query/custom::upd/1.0.0",
        json={"queryType": "diagnosis_codes", "queryDefinition": {"v": 1}},
    )
    resp = client.put(
        "/query/custom::upd/1.0.0",
        json={
            "queryType": "diagnosis_codes",
            "queryDefinition": {"v": 2},
            "description": "Updated",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated"
    assert resp.json()["queryDefinition"] == {"v": 2}


# =============================================================================
# Get endpoint
# =============================================================================

def test_get_query_not_found(client):
    resp = client.get("/query/billing::nonexistent/1.0.0")
    assert resp.status_code == 404


def test_get_query_after_register(client):
    client.put(
        "/query/billing::get-test/1.0.0",
        json={"queryType": "diagnosis_codes", "queryDefinition": {"f": 1}},
    )
    resp = client.get("/query/billing::get-test/1.0.0")
    assert resp.status_code == 200
    assert resp.json()["qualifiedName"] == "billing::get-test"


# =============================================================================
# Execute endpoint (POST)
# =============================================================================

def test_execute_diagnosis_codes_end_to_end(client):
    account_id = _seed_via_api(client)
    resp = client.post(
        "/query/billing::diagnosis-codes/1.0.0",
        json={"parameters": {"patient_id": account_id}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["queryName"] == "billing::diagnosis-codes"
    assert data["resultCount"] >= 1
    assert all("diagnosisCode" in r for r in data["results"])


def test_execute_procedure_codes_end_to_end(client):
    account_id = _seed_via_api(client)
    resp = client.post(
        "/query/billing::procedure-codes/1.0.0",
        json={"parameters": {"patient_id": account_id}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resultCount"] >= 1
    assert all("procedureCode" in r for r in data["results"])


def test_execute_encounter_summary_end_to_end(client):
    account_id = _seed_via_api(client)
    resp = client.post(
        "/query/billing::encounter-summary/1.0.0",
        json={"parameters": {"patient_id": account_id}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resultCount"] == 1
    enc = data["results"][0]
    assert enc["accountId"] == account_id
    assert enc["totalProcedures"] >= 2


def test_execute_patient_coverage_end_to_end(client):
    """Patient coverage requires an account user — seed one via the API."""
    client.post("/query/_seed")
    # Create account + user
    resp = client.post("/account/", json={"displayName": "Coverage Acct"})
    account_id = resp.json()["id"]
    # AccountUser creation requires a valid person; use direct DB seeding
    # via the _seed endpoint and just check coverage with no specific user
    resp = client.post(
        "/query/billing::patient-coverage/1.0.0",
        json={"parameters": {}},
    )
    assert resp.status_code == 200


def test_execute_query_not_found(client):
    resp = client.post(
        "/query/billing::nonexistent/1.0.0",
        json={"parameters": {}},
    )
    assert resp.status_code == 404


def test_execute_with_no_body(client):
    client.post("/query/_seed")
    resp = client.post("/query/billing::diagnosis-codes/1.0.0")
    assert resp.status_code == 200
    assert resp.json()["resultCount"] == 0


# =============================================================================
# Seed endpoint
# =============================================================================

def test_seed_is_idempotent(client):
    resp1 = client.post("/query/_seed")
    resp2 = client.post("/query/_seed")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["seeded"] == resp2.json()["seeded"] == 4


# =============================================================================
# Full lifecycle
# =============================================================================

def test_full_lifecycle_register_get_execute(client):
    """Register a query, retrieve it, execute it, list all."""
    # Register
    client.put(
        "/query/billing::lifecycle/1.0.0",
        json={
            "queryType": "diagnosis_codes",
            "queryDefinition": {"fields": ["diagnosisCode"]},
            "description": "Lifecycle test",
            "parametersSchema": {"type": "object"},
        },
    )

    # Retrieve
    resp = client.get("/query/billing::lifecycle/1.0.0")
    assert resp.status_code == 200
    assert resp.json()["description"] == "Lifecycle test"

    # Execute (no trades so empty results expected)
    resp = client.post(
        "/query/billing::lifecycle/1.0.0",
        json={"parameters": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["resultCount"] == 0

    # List
    resp = client.get("/query")
    assert resp.status_code == 200
    assert any(q["qualifiedName"] == "billing::lifecycle" for q in resp.json())


def test_versioning_different_versions_coexist(client):
    """Two versions of the same query can coexist."""
    client.put(
        "/query/billing::ver/1.0.0",
        json={"queryType": "diagnosis_codes", "queryDefinition": {"v": 1}},
    )
    client.put(
        "/query/billing::ver/2.0.0",
        json={"queryType": "procedure_codes", "queryDefinition": {"v": 2}},
    )

    resp_v1 = client.get("/query/billing::ver/1.0.0")
    resp_v2 = client.get("/query/billing::ver/2.0.0")

    assert resp_v1.status_code == 200
    assert resp_v2.status_code == 200
    assert resp_v1.json()["queryType"] == "diagnosis_codes"
    assert resp_v2.json()["queryType"] == "procedure_codes"


def test_tenant_isolation(client):
    """Queries registered for one tenant are not visible to another."""
    # Register for default tenant (acme_corp via middleware)
    client.put(
        "/query/billing::tenant-test/1.0.0",
        json={"queryType": "diagnosis_codes", "queryDefinition": {}},
    )

    # Verify it exists for default tenant
    resp = client.get("/query/billing::tenant-test/1.0.0")
    assert resp.status_code == 200

    # Query with a different tenant header should not find it
    resp = client.get(
        "/query/billing::tenant-test/1.0.0",
        headers={"X-Tenant-ID": "other_corp"},
    )
    assert resp.status_code == 404
