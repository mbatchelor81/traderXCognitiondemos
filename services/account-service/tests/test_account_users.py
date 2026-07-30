"""Account user endpoint tests. people-service is always mocked."""

from unittest.mock import patch

import httpx

from tests.conftest import TEST_TENANT_ID

PEOPLE_VALIDATE = "app.routes.accounts.people_client.validate_person"


def _add_user(client, account_id, username):
    with patch(PEOPLE_VALIDATE, return_value=True):
        return client.post(
            "/accountuser/", json={"accountId": account_id, "username": username}
        )


def test_list_account_users_empty(client):
    resp = client.get("/accountuser/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_account_user(client):
    resp = _add_user(client, 22214, "jsmith")
    assert resp.status_code == 200
    assert resp.json() == {
        "accountId": 22214,
        "tenant_id": TEST_TENANT_ID,
        "username": "jsmith",
    }


def test_create_account_user_is_idempotent(client):
    _add_user(client, 22214, "jsmith")
    _add_user(client, 22214, "jsmith")
    assert len(client.get("/accountuser/").json()) == 1


def test_list_account_users_filtered_by_account_id(client):
    _add_user(client, 22214, "jsmith")
    _add_user(client, 22214, "jdoe")
    _add_user(client, 11413, "mwilliams")

    resp = client.get("/accountuser/", params={"accountId": 22214})
    assert resp.status_code == 200
    usernames = sorted(u["username"] for u in resp.json())
    assert usernames == ["jdoe", "jsmith"]

    assert client.get("/accountuser/", params={"accountId": 99999}).json() == []


def test_create_account_user_requires_valid_payload(client):
    resp = client.post("/accountuser/", json={"username": "jsmith"})
    assert resp.status_code == 422


@patch(PEOPLE_VALIDATE, return_value=False)
def test_create_account_user_rejects_unknown_person(mock_validate, client):
    resp = client.post(
        "/accountuser/", json={"accountId": 22214, "username": "nobody"}
    )
    assert resp.status_code == 400
    assert "nobody" in resp.json()["detail"]
    assert client.get("/accountuser/").json() == []


@patch("app.clients.people_client.httpx.get")
def test_create_account_user_returns_503_when_people_service_down(mock_get, client):
    mock_get.side_effect = httpx.ConnectError("connection refused")

    resp = client.post(
        "/accountuser/", json={"accountId": 22214, "username": "jsmith"}
    )
    assert resp.status_code == 503
    assert "people-service" in resp.json()["detail"]
    assert client.get("/accountuser/").json() == []


@patch("app.clients.people_client.httpx.get")
def test_people_client_sends_logon_id_and_correlation_id(mock_get, client):
    mock_get.return_value = httpx.Response(
        200, json={"IsValid": True}, request=httpx.Request("GET", "http://peer")
    )

    resp = client.post(
        "/accountuser/",
        json={"accountId": 22214, "username": "jsmith"},
        headers={"X-Correlation-ID": "corr-xyz"},
    )
    assert resp.status_code == 200

    kwargs = mock_get.call_args.kwargs
    assert kwargs["params"] == {"LogonId": "jsmith"}
    assert kwargs["headers"]["X-Correlation-ID"] == "corr-xyz"
    assert kwargs["headers"]["X-Tenant-ID"] == TEST_TENANT_ID
    assert mock_get.call_args.args[0].endswith("/people/ValidatePerson")


def test_update_account_user(client):
    _add_user(client, 22214, "jsmith")

    resp = client.put(
        "/accountuser/", json={"accountId": 22214, "username": "jsmith"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "jsmith"
