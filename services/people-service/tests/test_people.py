"""Endpoint tests for the person directory."""

import pytest


def test_get_person_by_logon_id(client):
    response = client.get("/people/GetPerson", params={"LogonId": "jsmith"})
    assert response.status_code == 200
    assert response.json() == {
        "LogonId": "jsmith",
        "FullName": "John Smith",
        "Email": "john.smith@example.com",
        "EmployeeId": "EMP001",
        "Department": "Trading",
        "PhotoUrl": "https://randomuser.me/api/portraits/men/1.jpg",
    }


def test_get_person_by_employee_id(client):
    response = client.get("/people/GetPerson", params={"EmployeeId": "EMP002"})
    assert response.status_code == 200
    assert response.json()["LogonId"] == "jdoe"


def test_get_person_unknown_logon_id_returns_404(client):
    response = client.get("/people/GetPerson", params={"LogonId": "nobody"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


def test_get_person_without_identifier_returns_400(client):
    response = client.get("/people/GetPerson")
    assert response.status_code == 400
    assert response.json()["detail"] == "Either LogonId or EmployeeId must be provided"


def test_get_matching_people_returns_matches(client):
    response = client.get("/people/GetMatchingPeople", params={"SearchText": "smith"})
    assert response.status_code == 200
    logon_ids = [p["LogonId"] for p in response.json()["People"]]
    assert "jsmith" in logon_ids


def test_get_matching_people_no_matches_returns_empty_list(client):
    response = client.get("/people/GetMatchingPeople", params={"SearchText": "zzzzz"})
    assert response.status_code == 200
    assert response.json() == {"People": []}


def test_get_matching_people_respects_take(client):
    unlimited = client.get("/people/GetMatchingPeople", params={"SearchText": "son"})
    assert len(unlimited.json()["People"]) > 1

    limited = client.get(
        "/people/GetMatchingPeople", params={"SearchText": "son", "Take": 1}
    )
    assert limited.status_code == 200
    assert len(limited.json()["People"]) == 1


@pytest.mark.parametrize("params", [{}, {"SearchText": ""}])
def test_get_matching_people_requires_search_text(client, params):
    response = client.get("/people/GetMatchingPeople", params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "SearchText must be provided"


def test_get_matching_people_rejects_short_search_text(client):
    response = client.get("/people/GetMatchingPeople", params={"SearchText": "js"})
    assert response.status_code == 400
    assert response.json()["detail"] == "SearchText must be at least 3 characters long"


def test_get_matching_people_rejects_non_integer_take(client):
    response = client.get(
        "/people/GetMatchingPeople", params={"SearchText": "smith", "Take": "many"}
    )
    assert response.status_code == 422


def test_validate_person_known_logon_id(client):
    response = client.get("/people/ValidatePerson", params={"LogonId": "jsmith"})
    assert response.status_code == 200
    assert response.json() == {"IsValid": True}


def test_validate_person_unknown_logon_id(client):
    response = client.get("/people/ValidatePerson", params={"LogonId": "nobody"})
    assert response.status_code == 200
    assert response.json() == {"IsValid": False}


def test_validate_person_without_identifier_returns_400(client):
    response = client.get("/people/ValidatePerson")
    assert response.status_code == 400
    assert response.json()["detail"] == "Either LogonId or EmployeeId must be provided"
