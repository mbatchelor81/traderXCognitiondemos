"""Tests for position endpoints (GET /positions/ and GET /positions/{account_id})."""


def _create_account(client, name="Test Account"):
    """Helper to create an account and return its ID."""
    resp = client.post("/account/", json={"displayName": name})
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100):
    """Helper to submit a trade (which creates/updates a position)."""
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_list_positions_empty(client):
    """Listing positions for a tenant with no trades returns an empty list."""
    resp = client.get("/positions/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_positions_for_tenant(client):
    """Positions created via trades appear in GET /positions/."""
    acct_id = _create_account(client)
    _submit_trade(client, acct_id, security="AAPL", side="Buy", quantity=50)
    _submit_trade(client, acct_id, security="MSFT", side="Buy", quantity=30)

    resp = client.get("/positions/")
    assert resp.status_code == 200
    positions = resp.json()
    assert len(positions) == 2

    securities = {p["security"] for p in positions}
    assert securities == {"AAPL", "MSFT"}


def test_list_positions_by_account(client):
    """GET /positions/{account_id} returns only that account's positions."""
    acct1 = _create_account(client, "Account A")
    acct2 = _create_account(client, "Account B")

    _submit_trade(client, acct1, security="AAPL", side="Buy", quantity=10)
    _submit_trade(client, acct2, security="GOOG", side="Buy", quantity=20)

    resp = client.get(f"/positions/{acct1}")
    assert resp.status_code == 200
    positions = resp.json()
    assert len(positions) == 1
    assert positions[0]["security"] == "AAPL"
    assert positions[0]["accountId"] == acct1

    resp2 = client.get(f"/positions/{acct2}")
    assert resp2.status_code == 200
    positions2 = resp2.json()
    assert len(positions2) == 1
    assert positions2[0]["security"] == "GOOG"
    assert positions2[0]["accountId"] == acct2


def test_positions_nonexistent_account(client):
    """Requesting positions for a non-existent account returns an empty list."""
    resp = client.get("/positions/999999")
    assert resp.status_code == 200
    assert resp.json() == []


def test_position_quantity_accumulates(client):
    """Multiple buy trades for the same security accumulate quantity."""
    acct_id = _create_account(client)
    _submit_trade(client, acct_id, security="AAPL", side="Buy", quantity=50)
    _submit_trade(client, acct_id, security="AAPL", side="Buy", quantity=25)

    resp = client.get(f"/positions/{acct_id}")
    assert resp.status_code == 200
    positions = resp.json()
    assert len(positions) == 1
    assert positions[0]["security"] == "AAPL"
    assert positions[0]["quantity"] == 75
