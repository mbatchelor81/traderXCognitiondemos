"""Tests for POST /trade/validate endpoint."""
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_account(client, tenant="acme_corp"):
    """Create an account for the given tenant and return its id."""
    resp = client.post(
        "/account/",
        json={"displayName": "Test Account"},
        headers={"X-Tenant-ID": tenant},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Happy-path
# ---------------------------------------------------------------------------

def test_validate_valid_trade(client):
    account_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is True


def test_validate_valid_trade_with_price(client):
    account_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "MSFT",
            "side": "Sell",
            "quantity": 50,
            "price": 425.50,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is True


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------

def test_validate_invalid_security(client):
    account_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "DOESNOTEXIST",
            "side": "Buy",
            "quantity": 10,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 400
    assert "DOESNOTEXIST" in resp.json()["detail"]


def test_validate_invalid_side(client):
    account_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Short",
            "quantity": 10,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 400
    assert "side" in resp.json()["detail"].lower()


def test_validate_invalid_quantity_zero(client):
    account_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 0,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 400
    assert "quantity" in resp.json()["detail"].lower()


def test_validate_nonexistent_account(client):
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": 999999,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 10,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 400
    assert "999999" in resp.json()["detail"]


def test_validate_negative_price_rejected_by_schema(client):
    """Pydantic rejects price <= 0 before the handler runs."""
    account_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 10,
            "price": -5.0,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert resp.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

def test_validate_account_in_wrong_tenant(client):
    """Account created in tenant A must not be visible to tenant B."""
    account_id = _create_account(client, tenant="acme_corp")
    resp = client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 10,
        },
        headers={"X-Tenant-ID": "globex_inc"},
    )
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# No side-effects
# ---------------------------------------------------------------------------

def test_validate_does_not_create_trade(client):
    """Calling /trade/validate must not insert a trade record."""
    account_id = _create_account(client)
    client.post(
        "/trade/validate",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
        headers={"X-Tenant-ID": "acme_corp"},
    )
    trades = client.get("/trades/", headers={"X-Tenant-ID": "acme_corp"})
    assert trades.json() == []
