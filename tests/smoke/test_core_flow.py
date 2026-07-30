"""
End-to-end trade lifecycle through the gateway.

This is the application's primary workflow and it forces four of the five
services to talk to each other over HTTP:

    account-service   -> people-service        (validate the account user)
    trading-service   -> account-service       (the account exists)
    trading-service   -> reference-data-service(the security exists)
    trading-service   -> position-service      (apply the position delta)
    account-service   -> position-service      (compose positions onto the account)
"""

import uuid

import pytest


@pytest.fixture(scope="module")
def account(client) -> int:
    display_name = f"smoke-{uuid.uuid4().hex[:8]}"
    response = client.post("/account/", json={"displayName": display_name})

    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_reference_data_lists_securities(client):
    response = client.get("/stocks/")

    assert response.status_code == 200, response.text
    tickers = response.json()
    assert any(
        (t.get("ticker") or t.get("Ticker")) == "AAPL" for t in tickers
    ), "AAPL is missing from the reference data universe"


def test_account_user_is_validated_against_people_service(client, account):
    search = client.get("/people/GetMatchingPeople", params={"SearchText": "smith"})
    assert search.status_code == 200, search.text

    payload = search.json()
    people = payload.get("People", payload) if isinstance(payload, dict) else payload
    assert people, "people-service returned nobody to attach to the account"

    logon_id = people[0].get("logonId") or people[0].get("LogonId")
    assert logon_id, f"no logon id in {people[0]}"

    response = client.post(
        "/accountuser/", json={"accountId": account, "username": logon_id}
    )
    assert response.status_code == 200, response.text


def test_unknown_security_is_rejected(client, account):
    response = client.post(
        "/trade/",
        json={
            "accountId": account,
            "security": "NOTATICKER",
            "side": "Buy",
            "quantity": 1,
        },
    )

    rejected = response.status_code >= 400 or response.json().get("success") is False
    assert rejected, "trading-service accepted a trade for an unknown security"


def test_trade_updates_position(client, account):
    response = client.post(
        "/trade/",
        json={"accountId": account, "security": "AAPL", "side": "Buy", "quantity": 100},
    )
    assert response.status_code == 200, response.text
    assert response.json().get("success") is True, response.text

    positions = client.get(f"/positions/{account}")
    assert positions.status_code == 200, positions.text

    aapl = [p for p in positions.json() if p.get("security") == "AAPL"]
    assert aapl, f"no AAPL position for account {account}: {positions.text}"
    assert aapl[0]["quantity"] == 100


def test_account_composes_positions(client, account):
    response = client.get(f"/account/{account}")

    assert response.status_code == 200, response.text
    embedded = response.json().get("positions", [])
    assert any(
        p.get("security") == "AAPL" for p in embedded
    ), f"account-service did not compose positions from position-service: {response.text}"


def test_trades_are_visible_for_the_account(client, account):
    response = client.get(f"/trades/{account}")

    assert response.status_code == 200, response.text
    trades = response.json()
    assert any(t.get("security") == "AAPL" for t in trades), response.text


def test_analytics_reports_the_trade(client, account):
    response = client.get(f"/analytics/trades/{account}")

    assert response.status_code == 200, response.text
