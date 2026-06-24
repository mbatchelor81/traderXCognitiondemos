"""Tests for POST /trade/validate endpoint."""
import pytest


VALID_PAYLOAD = {
    "accountId": None,  # filled per-test after account creation
    "security": "AAPL",
    "side": "Buy",
    "quantity": 100,
    "price": 150.00,
}


def _create_account(client):
    resp = client.post("/account/", json={"displayName": "Validate Test"})
    assert resp.status_code == 200
    return resp.json()["id"]


def _validate(client, overrides=None, account_id=None):
    payload = {**VALID_PAYLOAD, **(overrides or {})}
    if account_id is not None:
        payload["accountId"] = account_id
    return client.post("/trade/validate", json=payload)


# ---- Happy path ----

def test_validate_valid_trade(client):
    acct_id = _create_account(client)
    resp = _validate(client, account_id=acct_id)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["errors"] == []


# ---- Ticker validation ----

def test_validate_invalid_ticker(client):
    acct_id = _create_account(client)
    resp = _validate(client, {"security": "INVALID_TICKER"}, account_id=acct_id)
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("Security" in e for e in errors)


# ---- Account validation ----

def test_validate_nonexistent_account(client):
    resp = _validate(client, {"accountId": 999999})
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("Account" in e for e in errors)


# ---- Tenant isolation ----

def test_validate_account_wrong_tenant(client):
    acct_id = _create_account(client)
    resp = client.post(
        "/trade/validate",
        json={**VALID_PAYLOAD, "accountId": acct_id},
        headers={"X-Tenant-ID": "other_tenant"},
    )
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("Account" in e for e in errors)


# ---- Quantity validation ----

def test_validate_zero_quantity(client):
    acct_id = _create_account(client)
    resp = _validate(client, {"quantity": 0}, account_id=acct_id)
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("quantity" in e for e in errors)


def test_validate_negative_quantity(client):
    acct_id = _create_account(client)
    resp = _validate(client, {"quantity": -5}, account_id=acct_id)
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("quantity" in e for e in errors)


# ---- Price validation ----

def test_validate_zero_price(client):
    acct_id = _create_account(client)
    resp = _validate(client, {"price": 0.0}, account_id=acct_id)
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("price" in e for e in errors)


def test_validate_negative_price(client):
    acct_id = _create_account(client)
    resp = _validate(client, {"price": -10.0}, account_id=acct_id)
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("price" in e for e in errors)


def test_validate_excessive_price(client):
    acct_id = _create_account(client)
    resp = _validate(client, {"price": 9999999.99}, account_id=acct_id)
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert any("price" in e for e in errors)


# ---- Multiple errors returned together ----

def test_validate_multiple_errors(client):
    resp = _validate(client, {
        "accountId": 999999,
        "security": "FAKE",
        "quantity": -1,
        "price": -1.0,
        "side": "InvalidSide",
    })
    assert resp.status_code == 400
    errors = resp.json()["detail"]["errors"]
    assert len(errors) >= 3
