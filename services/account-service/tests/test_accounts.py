"""Tests for Account Service."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "account-service"
    assert data["tenant"] == "test_tenant"


def test_create_account(client):
    response = client.post("/account/", json={"id": 1001, "displayName": "Test Account"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1001
    assert data["displayName"] == "Test Account"


def test_list_accounts_empty(client):
    response = client.get("/account/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_account(client):
    client.post("/account/", json={"id": 2001, "displayName": "My Account"})
    response = client.get("/account/2001")
    assert response.status_code == 200
    assert response.json()["displayName"] == "My Account"


def test_get_account_not_found(client):
    response = client.get("/account/9999")
    assert response.status_code == 404
