"""
Trade submission and query tests.

Every cross-service call is mocked — the suite passes with no peer service
running.
"""

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest

from app.clients.http_client import PeerServiceError
from app.config import TENANT_ID
from app.models.trade import Trade
from tests.conftest import TEST_ACCOUNT_ID


@contextmanager
def peers(
    *,
    account_exists=True,
    account_has_users=True,
    security_exists=True,
    position_quantity=0,
    apply_side_effect=None,
    apply_return=None,
):
    """Patch every outbound peer call used by trade processing."""
    applied = apply_return if apply_return is not None else {
        "accountId": TEST_ACCOUNT_ID,
        "tenant_id": TENANT_ID,
        "security": "AAPL",
        "quantity": 100,
        "updated": "2026-01-01T00:00:00",
    }
    with patch(
        "app.clients.account_client.account_exists",
        new=AsyncMock(return_value=account_exists),
    ) as m_exists, patch(
        "app.clients.account_client.account_has_users",
        new=AsyncMock(return_value=account_has_users),
    ) as m_users, patch(
        "app.clients.reference_data_client.security_exists",
        new=AsyncMock(return_value=security_exists),
    ) as m_security, patch(
        "app.clients.position_client.get_position_quantity",
        new=AsyncMock(return_value=position_quantity),
    ) as m_get_position, patch(
        "app.clients.position_client.apply_position_delta",
        new=AsyncMock(return_value=applied, side_effect=apply_side_effect),
    ) as m_apply:
        yield {
            "account_exists": m_exists,
            "account_has_users": m_users,
            "security_exists": m_security,
            "get_position_quantity": m_get_position,
            "apply_position_delta": m_apply,
        }


def submit(client, **overrides):
    body = {
        "accountId": TEST_ACCOUNT_ID,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    }
    body.update(overrides)
    return client.post("/trade/", json=body)


def test_submit_buy_trade_settles_and_applies_position(client, db_session):
    with peers() as mocks:
        response = submit(client)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["trade"]["state"] == "Settled"
    assert body["trade"]["accountId"] == TEST_ACCOUNT_ID
    assert body["trade"]["side"] == "Buy"
    assert body["position"]["security"] == "AAPL"

    mocks["apply_position_delta"].assert_awaited_once_with(TEST_ACCOUNT_ID, "AAPL", 100)

    stored = db_session.query(Trade).all()
    assert len(stored) == 1
    assert stored[0].tenant_id == TENANT_ID


def test_submit_sell_trade_sends_a_negative_delta(client):
    with peers(position_quantity=500) as mocks:
        response = submit(client, side="Sell", quantity=25)

    assert response.status_code == 200
    mocks["apply_position_delta"].assert_awaited_once_with(TEST_ACCOUNT_ID, "AAPL", -25)


def test_sell_beyond_current_position_is_still_accepted(client):
    """The monolith warns but accepts oversold trades — behaviour is preserved."""
    with peers(position_quantity=5):
        response = submit(client, side="Sell", quantity=1000)

    assert response.status_code == 200
    assert response.json()["trade"]["side"] == "Sell"


def test_unknown_account_is_rejected(client, db_session):
    with peers(account_exists=False):
        response = submit(client)

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
    assert db_session.query(Trade).count() == 0


def test_account_without_users_is_rejected(client):
    with peers(account_has_users=False):
        response = submit(client)

    assert response.status_code == 400
    assert "no users" in response.json()["detail"]


def test_unknown_security_is_rejected(client):
    with peers(security_exists=False):
        response = submit(client, security="NOPE")

    assert response.status_code == 400
    assert "reference data" in response.json()["detail"]


def test_invalid_side_is_rejected(client):
    with peers():
        response = submit(client, side="Hold")

    assert response.status_code == 400
    assert "Invalid trade side" in response.json()["detail"]


def test_zero_quantity_is_rejected(client):
    with peers():
        response = submit(client, quantity=0)

    assert response.status_code == 400
    assert "Invalid trade quantity" in response.json()["detail"]


def test_malformed_body_returns_422(client):
    response = client.post("/trade/", json={"accountId": "abc", "security": "AAPL"})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "failing_peer",
    ["account_exists", "security_exists", "apply_position_delta"],
)
def test_unreachable_peer_fails_the_trade_with_502(client, db_session, failing_peer):
    error = PeerServiceError("position-service", "http://localhost:8003", "timeout")
    kwargs = {}
    if failing_peer == "apply_position_delta":
        kwargs["apply_side_effect"] = error

    with peers(**kwargs) as mocks:
        if failing_peer != "apply_position_delta":
            mocks[failing_peer].side_effect = error
        response = submit(client)

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]
    assert db_session.query(Trade).count() == 0


def test_mismatched_tenant_header_is_rejected_on_trade_submission(client):
    with peers():
        response = client.post(
            "/trade/",
            json={
                "accountId": TEST_ACCOUNT_ID,
                "security": "AAPL",
                "side": "Buy",
                "quantity": 100,
            },
            headers={"X-Tenant-ID": "other_tenant"},
        )

    assert response.status_code == 403


def test_list_all_trades_returns_newest_first(client, seeded_trades):
    response = client.get("/trades/")

    assert response.status_code == 200
    trades = response.json()
    assert len(trades) == 3
    assert trades[0]["security"] == "MSFT"
    assert all(t["tenant_id"] == TENANT_ID for t in trades)


def test_list_trades_by_account(client, seeded_trades):
    response = client.get(f"/trades/{TEST_ACCOUNT_ID}")

    assert response.status_code == 200
    trades = response.json()
    assert len(trades) == 2
    assert {t["side"] for t in trades} == {"Buy", "Sell"}


def test_list_trades_for_unknown_account_is_empty(client, seeded_trades):
    response = client.get("/trades/99999")

    assert response.status_code == 200
    assert response.json() == []


def test_trades_of_another_tenant_are_never_returned(client, db_session, seeded_trades):
    db_session.add(
        Trade(
            tenant_id="other_tenant",
            account_id=TEST_ACCOUNT_ID,
            security="TSLA",
            side="Buy",
            quantity=10,
            state="Settled",
        )
    )
    db_session.commit()

    response = client.get("/trades/")

    assert response.status_code == 200
    assert all(t["tenant_id"] == TENANT_ID for t in response.json())
    assert "TSLA" not in [t["security"] for t in response.json()]
