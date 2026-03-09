"""Test account CRUD for users-service."""


def test_create_account(client):
    response = client.post("/account/", json={
        "id": 1001,
        "displayName": "Test Account",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1001
    assert data["displayName"] == "Test Account"
    assert data["tenant_id"] == "acme_corp"


def test_list_accounts_empty(client):
    response = client.get("/account/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_accounts_after_create(client):
    client.post("/account/", json={"id": 2001, "displayName": "Acct A"})
    client.post("/account/", json={"id": 2002, "displayName": "Acct B"})
    response = client.get("/account/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_account_by_id(client):
    client.post("/account/", json={"id": 3001, "displayName": "Lookup Acct"})
    response = client.get("/account/3001")
    assert response.status_code == 200
    assert response.json()["displayName"] == "Lookup Acct"


def test_get_account_not_found(client):
    response = client.get("/account/99999")
    assert response.status_code == 404


def test_tenant_mismatch_rejected(client):
    response = client.get("/health", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
