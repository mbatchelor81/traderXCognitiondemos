"""Trade state machine tests."""

import pytest

from app.config import TENANT_ID
from app.models.trade import Trade
from app.services import trade_processor
from tests.conftest import TEST_ACCOUNT_ID


@pytest.mark.parametrize(
    "current,new,expected",
    [
        ("New", "Processing", True),
        ("New", "Cancelled", True),
        ("New", "Settled", False),
        ("Processing", "Settled", True),
        ("Processing", "Cancelled", True),
        ("Processing", "New", False),
        ("Settled", "Cancelled", False),
        ("Cancelled", "Processing", False),
    ],
)
def test_can_transition(current, new, expected):
    assert trade_processor.can_transition(current, new) is expected


def _new_trade(db_session, state="New"):
    trade = Trade(
        tenant_id=TENANT_ID,
        account_id=TEST_ACCOUNT_ID,
        security="AAPL",
        side="Buy",
        quantity=10,
        state=state,
    )
    db_session.add(trade)
    db_session.commit()
    return trade


def test_valid_transition_is_applied(db_session):
    trade = _new_trade(db_session)

    assert trade_processor.transition_trade_state(db_session, trade, "Processing")
    assert trade.state == "Processing"


def test_invalid_transition_leaves_state_untouched(db_session):
    trade = _new_trade(db_session, state="Settled")

    assert not trade_processor.transition_trade_state(db_session, trade, "Processing")
    assert trade.state == "Settled"


def test_settle_pending_trades(db_session):
    _new_trade(db_session, state="Processing")
    _new_trade(db_session, state="Processing")
    _new_trade(db_session, state="New")

    assert trade_processor.settle_pending_trades(db_session, TENANT_ID) == 2
    assert len(trade_processor.get_trades_by_state(db_session, "Settled", TENANT_ID)) == 2


def test_cancel_stale_trades(db_session):
    from datetime import datetime, timedelta

    stale = _new_trade(db_session)
    stale.created = datetime.utcnow() - timedelta(hours=48)
    db_session.commit()

    assert trade_processor.cancel_stale_trades(db_session, TENANT_ID) == 1
    assert stale.state == "Cancelled"


def test_trade_restrictions_come_from_config():
    restrictions = trade_processor.get_tenant_trade_restrictions()

    assert restrictions["allowedSides"] == ["Buy", "Sell"]
    assert restrictions["autoSettle"] is True
