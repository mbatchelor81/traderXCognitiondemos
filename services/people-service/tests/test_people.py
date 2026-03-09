"""Tests for People Service."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "people-service"
    assert data["tenant"] == "test_tenant"


def test_get_matching_people(client):
    response = client.get("/people/GetMatchingPeople", params={"SearchText": "John"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_validate_person_not_found(client):
    response = client.get("/people/ValidatePerson", params={"LogonId": "nonexistent_user_xyz"})
    assert response.status_code == 200
    data = response.json()
    assert data["IsValid"] is False


def test_get_person_not_found(client):
    response = client.get("/people/GetPerson", params={"LogonId": "nonexistent_user_xyz"})
    assert response.status_code == 404
