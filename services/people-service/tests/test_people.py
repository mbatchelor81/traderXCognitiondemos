"""Test People lookup operations."""


def test_get_person(client):
    response = client.get("/people/GetPerson", params={"LogonId": "jsmith"})
    assert response.status_code == 200
    data = response.json()
    assert data["LogonId"] == "jsmith"
    assert "FullName" in data


def test_get_person_not_found(client):
    response = client.get("/people/GetPerson", params={"LogonId": "nonexistent_user"})
    assert response.status_code == 404


def test_get_matching_people(client):
    response = client.get("/people/GetMatchingPeople", params={"Search": "smith"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_validate_person_valid(client):
    response = client.get("/people/ValidatePerson", params={"LogonId": "jsmith"})
    assert response.status_code == 200
    data = response.json()
    assert data["IsValid"] is True


def test_validate_person_invalid(client):
    response = client.get("/people/ValidatePerson", params={"LogonId": "nonexistent"})
    assert response.status_code == 200
    data = response.json()
    assert data["IsValid"] is False


def test_tenant_mismatch_rejected(client):
    response = client.get("/people/GetMatchingPeople", params={"Search": "test"}, headers={"X-Tenant-ID": "wrong_tenant"})
    assert response.status_code == 403
