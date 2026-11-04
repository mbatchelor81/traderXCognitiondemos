from datetime import timedelta

import pytest

from app.models.position import Position
from app.models.trade import Trade
from app.services.trade_processor import cancel_stale_trades
from app.utils.helpers import now_utc
from tests.conftest import TestingSessionLocal

TENANT = "initech"


def _submit(client, account_id, security, side, quantity):
    resp = client.post("/trade/", headers={"X-Tenant-ID": TENANT}, json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["trade"]["state"] == "Processing"
    return body["trade"]["id"]


def _position_qty(db, account_id, security):
    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == TENANT,
    ).first()
    return position.quantity


def _age_trades(db, trade_ids, hours=48):
    for trade in db.query(Trade).filter(Trade.id.in_(trade_ids)):
        trade.created = now_utc() - timedelta(hours=hours)
    db.commit()


@pytest.fixture()
def account_id(client):
    resp = client.post("/account/", headers={"X-Tenant-ID": TENANT},
                       json={"displayName": "Initech Trading"})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_cancel_stale_buy_reverses_position(client, account_id):
    _submit(client, account_id, "MSFT", "Buy", 200)
    stale_id = _submit(client, account_id, "MSFT", "Buy", 500)

    db = TestingSessionLocal()
    try:
        assert _position_qty(db, account_id, "MSFT") == 700
        _age_trades(db, [stale_id])

        assert cancel_stale_trades(db, TENANT) == 1

        assert db.get(Trade, stale_id).state == "Cancelled"
        assert _position_qty(db, account_id, "MSFT") == 200
    finally:
        db.close()


def test_cancel_stale_sell_reverses_position(client, account_id):
    _submit(client, account_id, "AAPL", "Buy", 300)
    stale_id = _submit(client, account_id, "AAPL", "Sell", 100)

    db = TestingSessionLocal()
    try:
        assert _position_qty(db, account_id, "AAPL") == 200
        _age_trades(db, [stale_id])

        assert cancel_stale_trades(db, TENANT) == 1

        assert _position_qty(db, account_id, "AAPL") == 300
    finally:
        db.close()


def test_cancel_stale_new_trade_leaves_position_untouched(client, account_id):
    _submit(client, account_id, "IBM", "Buy", 50)

    db = TestingSessionLocal()
    try:
        new_trade = Trade(tenant_id=TENANT, account_id=account_id,
                          security="IBM", side="Buy", quantity=25,
                          state="New", created=now_utc() - timedelta(hours=48),
                          updated=now_utc())
        db.add(new_trade)
        db.commit()
        _age_trades(db, [new_trade.id])

        assert cancel_stale_trades(db, TENANT) == 1

        assert db.get(Trade, new_trade.id).state == "Cancelled"
        assert _position_qty(db, account_id, "IBM") == 50
    finally:
        db.close()


def test_recent_processing_trade_is_not_cancelled(client, account_id):
    trade_id = _submit(client, account_id, "MSFT", "Buy", 10)

    db = TestingSessionLocal()
    try:
        assert cancel_stale_trades(db, TENANT) == 0
        assert db.get(Trade, trade_id).state == "Processing"
        assert _position_qty(db, account_id, "MSFT") == 10
    finally:
        db.close()
