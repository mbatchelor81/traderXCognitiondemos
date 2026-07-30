"""Unit tests for the position service layer and seeding."""
from app.models.position import Position
from app.seed import seed_positions
from app.services import position_service
from app.utils.helpers import now_utc
from tests.conftest import TEST_TENANT_ID


def test_get_current_position_quantity_defaults_to_zero(db_session):
    assert position_service.get_current_position_quantity(
        db_session, 22214, "AAPL", TEST_TENANT_ID) == 0


def test_update_position_upserts_and_accumulates(db_session):
    position_service.update_position(db_session, 22214, "AAPL", 100, TEST_TENANT_ID)
    position = position_service.update_position(
        db_session, 22214, "AAPL", -30, TEST_TENANT_ID)
    db_session.commit()

    assert position.quantity == 70
    assert position_service.get_current_position_quantity(
        db_session, 22214, "AAPL", TEST_TENANT_ID) == 70


def test_update_position_refreshes_updated_timestamp(db_session):
    position = position_service.update_position(
        db_session, 22214, "AAPL", 10, TEST_TENANT_ID)
    first = position.updated
    position = position_service.update_position(
        db_session, 22214, "AAPL", 10, TEST_TENANT_ID)
    assert position.updated >= first


def test_queries_filter_by_tenant(db_session):
    db_session.add(Position(account_id=22214, tenant_id=TEST_TENANT_ID,
                            security="AAPL", quantity=70, updated=now_utc()))
    db_session.add(Position(account_id=22214, tenant_id="other_tenant",
                            security="AAPL", quantity=999, updated=now_utc()))
    db_session.commit()

    for_tenant = position_service.get_positions_for_account(
        db_session, 22214, TEST_TENANT_ID)
    assert [p.quantity for p in for_tenant] == [70]
    assert [p.quantity for p in position_service.get_all_positions(
        db_session, TEST_TENANT_ID)] == [70]


def test_recalculate_ignores_other_accounts(db_session):
    db_session.add(Position(account_id=11413, tenant_id=TEST_TENANT_ID,
                            security="AAPL", quantity=500, updated=now_utc()))
    db_session.commit()

    position_service.recalculate_positions(
        db_session, 22214,
        [{"security": "AAPL", "side": "Buy", "quantity": 10}],
        TEST_TENANT_ID,
    )

    assert position_service.get_current_position_quantity(
        db_session, 11413, "AAPL", TEST_TENANT_ID) == 500
    assert position_service.get_current_position_quantity(
        db_session, 22214, "AAPL", TEST_TENANT_ID) == 10


def test_seed_positions_inserts_tenant_rows(db_session):
    count = seed_positions(db_session, "acme_corp")
    db_session.commit()

    assert count == 7
    positions = position_service.get_all_positions(db_session, "acme_corp")
    assert len(positions) == 7
    assert {p.security for p in positions} == {
        "AAPL", "MSFT", "GOOGL", "TSLA", "JPM", "BAC", "GS"}


def test_seed_positions_falls_back_to_acme_shape(db_session):
    count = seed_positions(db_session, "unknown_tenant")
    db_session.commit()

    assert count == 7
    assert len(position_service.get_all_positions(db_session, "unknown_tenant")) == 7
