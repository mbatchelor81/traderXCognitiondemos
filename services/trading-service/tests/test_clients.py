"""
Peer client tests. The HTTP transport is mocked, so no peer service is needed.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.clients import account_client, position_client, reference_data_client
from app.clients.http_client import PeerServiceError
from app.config import TENANT_ID


def _response(status_code: int, json_body=None) -> httpx.Response:
    return httpx.Response(
        status_code, json=json_body, request=httpx.Request("GET", "http://peer/")
    )


def _transport(response=None, side_effect=None):
    return patch.object(
        httpx.AsyncClient,
        "request",
        new=AsyncMock(return_value=response, side_effect=side_effect),
    )


def run(coro):
    """Drive a client coroutine to completion without an async test plugin."""
    return asyncio.run(coro)


def test_account_exists_true():
    with _transport(_response(200, {"exists": True})):
        assert run(account_client.account_exists(22214)) is True


def test_account_exists_false_on_404():
    with _transport(_response(404, {"detail": "not found"})):
        assert run(account_client.account_exists(1)) is False


def test_account_has_users():
    with _transport(_response(200, [{"username": "jsmith"}])):
        assert run(account_client.account_has_users(22214)) is True

    with _transport(_response(200, [])):
        assert run(account_client.account_has_users(22214)) is False


def test_security_exists():
    with _transport(_response(200, {"ticker": "AAPL", "companyName": "Apple Inc."})):
        assert run(reference_data_client.security_exists("AAPL")) is True

    with _transport(_response(404, {"detail": "unknown"})):
        assert run(reference_data_client.security_exists("NOPE")) is False


def test_position_quantity_is_read_from_the_account_positions():
    body = [
        {"accountId": 22214, "security": "AAPL", "quantity": 70},
        {"accountId": 22214, "security": "MSFT", "quantity": 250},
    ]
    with _transport(_response(200, body)):
        assert run(position_client.get_position_quantity(22214, "MSFT")) == 250
        assert run(position_client.get_position_quantity(22214, "TSLA")) == 0


def test_apply_position_delta_returns_the_updated_position():
    updated = {"accountId": 22214, "security": "AAPL", "quantity": 170}
    with _transport(_response(200, updated)) as mocked:
        assert run(position_client.apply_position_delta(22214, "AAPL", 100)) == updated

    _, kwargs = mocked.call_args
    assert kwargs["json"] == {
        "accountId": 22214,
        "security": "AAPL",
        "quantityDelta": 100,
    }
    assert kwargs["headers"]["X-Tenant-ID"] == TENANT_ID


def test_connection_error_raises_peer_service_error():
    with _transport(side_effect=httpx.ConnectError("connection refused")):
        with pytest.raises(PeerServiceError) as exc_info:
            run(account_client.account_exists(22214))

    assert exc_info.value.service == "account-service"


def test_peer_5xx_raises_peer_service_error():
    with _transport(_response(500, {"detail": "boom"})):
        with pytest.raises(PeerServiceError):
            run(reference_data_client.security_exists("AAPL"))
