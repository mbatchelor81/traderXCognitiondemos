"""Tests for account CRUD operations."""
import pytest


def test_createAccount(client):
    """Test creating an account via POST and retrieving it."""
    resp = client.post("/account/", json={"displayName": "Test Account"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["displayName"] == "Test Account"
    assert "id" in data

    # retrieve it
    account_id = data['id']
    resp2 = client.get(f"/account/{account_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched['displayName'] == "Test Account"
    assert fetched["id"] == account_id


def test_list_accounts_empty(client):
    r = client.get('/account/')
    assert r.status_code == 200
    assert r.json() == []


# =============================================================================
# Null-field endpoint tests
# =============================================================================

def test_list_accounts_with_null_fields_empty(client):
    """GET /account/null-fields/ returns empty list when no accounts have nulls."""
    # Create an account with a valid display name
    client.post("/account/", json={"displayName": "Good Account"})
    resp = client.get("/account/null-fields/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_accounts_with_null_fields_returns_null_accounts(client):
    """GET /account/null-fields/ returns accounts that have null display_name."""
    # Create an account with an empty display name
    client.post("/account/", json={"displayName": ""})
    # Create an account with a valid display name
    client.post("/account/", json={"displayName": "Good Account"})

    resp = client.get("/account/null-fields/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["displayName"] == ""


def test_validate_nulls_happy_path(client):
    """POST /account/validate-nulls/ returns correct diagnostics."""
    # Create two accounts: one with a name, one without
    resp1 = client.post("/account/", json={"displayName": "Named"})
    resp2 = client.post("/account/", json={"displayName": ""})
    id_named = resp1.json()["id"]
    id_empty = resp2.json()["id"]

    resp = client.post("/account/validate-nulls/",
                       json={"accountIds": [id_named, id_empty]})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2

    # First account should have no null fields
    assert results[0]["accountId"] == id_named
    assert results[0]["found"] is True
    assert results[0]["hasNullFields"] is False
    assert results[0]["nullFields"] == []

    # Second account should flag displayName as null
    assert results[1]["accountId"] == id_empty
    assert results[1]["found"] is True
    assert results[1]["hasNullFields"] is True
    assert "displayName" in results[1]["nullFields"]


def test_validate_nulls_missing_account(client):
    """POST /account/validate-nulls/ reports not-found for missing IDs."""
    resp = client.post("/account/validate-nulls/",
                       json={"accountIds": [99999]})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["found"] is False


def test_validate_nulls_empty_list(client):
    """POST /account/validate-nulls/ with empty list returns 400."""
    resp = client.post("/account/validate-nulls/",
                       json={"accountIds": []})
    assert resp.status_code == 400
