"""Test Position query operations."""


def test_list_positions_empty(client):
    response = client.get("/positions/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_positions(client, seed_positions):
    response = client.get("/positions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_list_positions_by_account(client, seed_positions):
    response = client.get("/positions/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(p["accountId"] == 1 for p in data)


def test_list_positions_by_account_no_results(client, seed_positions):
    response = client.get("/positions/999")
    assert response.status_code == 200
    assert response.json() == []


def test_tenant_mismatch_rejected(client):
    response = client.get("/positions/", headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
