"""Tests for account CRUD operations."""


def test_create_account(client):
    """Test creating an account."""
    response = client.post("/account/", json={"displayName": "Test Account"})
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "Test Account"
    assert data["tenant_id"] == "acme_corp"
    assert "id" in data


def test_list_accounts_empty(client):
    """Test listing accounts when none exist."""
    response = client.get("/account/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_accounts_after_create(client):
    """Test listing accounts after creating one."""
    client.post("/account/", json={"displayName": "Account A"})
    response = client.get("/account/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["displayName"] == "Account A"


def test_get_account_by_id(client):
    """Test getting account by ID."""
    create_resp = client.post("/account/", json={"displayName": "My Account"})
    account_id = create_resp.json()["id"]

    response = client.get(f"/account/{account_id}")
    assert response.status_code == 200
    assert response.json()["displayName"] == "My Account"


def test_get_account_not_found(client):
    """Test getting a non-existent account."""
    response = client.get("/account/99999")
    assert response.status_code == 404


def test_tenant_mismatch_rejected(client):
    """Test that mismatched tenant header is rejected with 403."""
    response = client.get("/health", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
