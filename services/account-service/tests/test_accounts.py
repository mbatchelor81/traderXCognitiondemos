"""Account CRUD endpoint tests. All peer service calls are mocked."""

from unittest.mock import patch

from tests.conftest import TEST_TENANT_ID


def _create_account(client, display_name="Test Account", account_id=None):
    body = {"displayName": display_name}
    if account_id is not None:
        body["id"] = account_id
    resp = client.post("/account/", json=body)
    assert resp.status_code == 200
    return resp.json()


def test_list_accounts_empty(client):
    resp = client.get("/account/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_account(client):
    data = _create_account(client, "Test Account")
    assert data["displayName"] == "Test Account"
    assert data["tenant_id"] == TEST_TENANT_ID
    assert data["id"] is not None


def test_create_account_with_explicit_id(client):
    data = _create_account(client, "Private Clients Fund TTXX", account_id=11413)
    assert data["id"] == 11413

    listed = client.get("/account/").json()
    assert [a["id"] for a in listed] == [11413]


def test_create_account_requires_display_name(client):
    resp = client.post("/account/", json={})
    assert resp.status_code == 422


def test_update_account_renames_existing_row(client):
    created = _create_account(client, "Old Name", account_id=22214)

    resp = client.put(
        "/account/", json={"id": created["id"], "displayName": "New Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["displayName"] == "New Name"

    listed = client.get("/account/").json()
    assert len(listed) == 1
    assert listed[0]["displayName"] == "New Name"


@patch("app.routes.accounts.position_client.get_positions_for_account")
def test_get_account_embeds_positions_from_position_service(mock_positions, client):
    mock_positions.return_value = [
        {"accountId": 22214, "security": "AAPL", "quantity": 70}
    ]
    created = _create_account(client, "Test Account 20", account_id=22214)

    resp = client.get(f"/account/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["displayName"] == "Test Account 20"
    assert body["positions"] == [
        {"accountId": 22214, "security": "AAPL", "quantity": 70}
    ]
    mock_positions.assert_called_once()


@patch("app.clients.position_client.httpx.get")
def test_get_account_tolerates_unreachable_position_service(mock_get, client):
    mock_get.side_effect = RuntimeError("connection refused")
    created = _create_account(client, "Test Account 20", account_id=22214)

    resp = client.get(f"/account/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["positions"] == []


@patch("app.routes.accounts.position_client.get_positions_for_account")
def test_get_account_propagates_correlation_id_to_peer(mock_positions, client):
    mock_positions.return_value = []
    created = _create_account(client, "Test Account 20", account_id=22214)

    client.get(
        f"/account/{created['id']}", headers={"X-Correlation-ID": "corr-abc"}
    )
    assert mock_positions.call_args.args == (22214, "corr-abc")


def test_get_account_not_found(client):
    resp = client.get("/account/999999")
    assert resp.status_code == 404
    assert "999999" in resp.json()["detail"]


def test_account_exists(client):
    created = _create_account(client, "Test Account 20", account_id=22214)

    assert client.get(f"/account/{created['id']}/exists").json() == {"exists": True}
    assert client.get("/account/999999/exists").json() == {"exists": False}
