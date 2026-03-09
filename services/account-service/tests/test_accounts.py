"""Test Account CRUD operations."""


def test_create_account(client):
    response = client.post("/account/", json={"displayName": "Test Account"})
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "Test Account"
    assert data["tenant_id"] == "test_tenant"
    assert "id" in data


def test_list_accounts(client):
    client.post("/account/", json={"displayName": "Account 1"})
    client.post("/account/", json={"displayName": "Account 2"})
    response = client.get("/account/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_account_by_id(client):
    create_resp = client.post("/account/", json={"displayName": "My Account"})
    account_id = create_resp.json()["id"]
    response = client.get(f"/account/{account_id}")
    assert response.status_code == 200
    assert response.json()["displayName"] == "My Account"


def test_get_account_not_found(client):
    response = client.get("/account/99999")
    assert response.status_code == 404


def test_update_account(client):
    create_resp = client.post("/account/", json={"displayName": "Original"})
    account_id = create_resp.json()["id"]
    response = client.put("/account/", json={"id": account_id, "displayName": "Updated"})
    assert response.status_code == 200
    assert response.json()["displayName"] == "Updated"


def test_tenant_mismatch_rejected(client):
    response = client.get("/account/", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403


def test_create_account_user_without_people_service(client):
    """Test creating account user when people service is unavailable (graceful degradation)."""
    create_resp = client.post("/account/", json={"displayName": "Test Account"})
    account_id = create_resp.json()["id"]
    response = client.post("/accountuser/", json={"accountId": account_id, "username": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["accountId"] == account_id
    assert data["username"] == "testuser"
