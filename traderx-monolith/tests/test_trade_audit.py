"""Tests for the trade audit trail feature."""

TENANT = "acme_corp"
OTHER_TENANT = "globex_inc"
HEADERS = {"X-Tenant-ID": TENANT}
OTHER_HEADERS = {"X-Tenant-ID": OTHER_TENANT}


def _create_account_and_trade(client):
    """Helper: create an account and submit a trade, return (account_id, trade_id)."""
    acct = client.post("/account/", json={"displayName": "Audit Test Account"},
                       headers=HEADERS)
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    }, headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    trade_id = body["trade"]["id"]
    return account_id, trade_id


def test_trade_audit_trail_created_on_submit(client):
    """Submit a trade, then GET the audit trail.
    Verify at least 3 entries (CREATED, STATE_CHANGE New->Processing,
    STATE_CHANGE Processing->Settled) in chronological order.
    """
    _account_id, trade_id = _create_account_and_trade(client)

    resp = client.get(f"/trades/{trade_id}/audit", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["tradeId"] == trade_id
    assert "currentState" in data
    audit_trail = data["auditTrail"]

    # Expect at least CREATED + STATE_CHANGE(New->Processing) + STATE_CHANGE(Processing->Settled)
    assert len(audit_trail) >= 3

    # Check event types present
    event_types = [entry["eventType"] for entry in audit_trail]
    assert "CREATED" in event_types
    assert "STATE_CHANGE" in event_types

    # Verify chronological order (timestamps non-decreasing)
    timestamps = [entry["timestamp"] for entry in audit_trail]
    assert timestamps == sorted(timestamps)

    # Verify the CREATED entry
    created_entry = next(e for e in audit_trail if e["eventType"] == "CREATED")
    assert created_entry["oldState"] is None
    assert created_entry["newState"] == "New"
    assert created_entry["tradeId"] == trade_id

    # Verify state change entries
    state_changes = [e for e in audit_trail if e["eventType"] == "STATE_CHANGE"]
    assert len(state_changes) >= 2
    # First state change: New -> Processing
    assert state_changes[0]["oldState"] == "New"
    assert state_changes[0]["newState"] == "Processing"
    # Second state change: Processing -> Settled
    assert state_changes[1]["oldState"] == "Processing"
    assert state_changes[1]["newState"] == "Settled"


def test_trade_audit_trail_404_for_missing_trade(client):
    """GET audit for non-existent trade_id returns 404."""
    resp = client.get("/trades/99999/audit", headers=HEADERS)
    assert resp.status_code == 404


def test_trade_audit_trail_tenant_isolation(client):
    """Submit a trade with one tenant, then request audit with a different
    X-Tenant-ID header — should return 404."""
    _account_id, trade_id = _create_account_and_trade(client)

    # Request audit using a different tenant
    resp = client.get(f"/trades/{trade_id}/audit", headers=OTHER_HEADERS)
    assert resp.status_code == 404
