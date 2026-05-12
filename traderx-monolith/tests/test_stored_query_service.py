"""Unit tests for stored query registration and execution."""

import pytest
from datetime import datetime

from app.models.account import Account, AccountUser
from app.models.position import Position
from app.models.trade import Trade
from app.services.stored_query_service import (
    QueryNotFoundError,
    UnsupportedQueryTypeError,
    delete_query,
    execute_query,
    get_query,
    list_queries,
    register_query,
    seed_billing_queries,
)
from tests.conftest import TestingSessionLocal


TENANT = "acme_corp"


@pytest.fixture()
def db():
    """Provide a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# =============================================================================
# Registration Tests
# =============================================================================

def test_register_query_creates_new(db):
    sq = register_query(
        db=db,
        qualified_name="billing::test",
        version="1.0.0",
        query_type="diagnosis_codes",
        query_definition={"fields": ["code"]},
        tenant_id=TENANT,
        description="Test query",
    )
    assert sq.id is not None
    assert sq.qualified_name == "billing::test"
    assert sq.version == "1.0.0"
    assert sq.query_type == "diagnosis_codes"
    assert sq.tenant_id == TENANT


def test_register_query_updates_existing(db):
    sq1 = register_query(
        db=db,
        qualified_name="billing::test",
        version="1.0.0",
        query_type="diagnosis_codes",
        query_definition={"fields": ["code"]},
        tenant_id=TENANT,
        description="Original",
    )
    sq2 = register_query(
        db=db,
        qualified_name="billing::test",
        version="1.0.0",
        query_type="diagnosis_codes",
        query_definition={"fields": ["code", "desc"]},
        tenant_id=TENANT,
        description="Updated",
    )
    assert sq2.id == sq1.id
    assert sq2.description == "Updated"


def test_register_query_different_versions(db):
    sq1 = register_query(
        db=db,
        qualified_name="billing::test",
        version="1.0.0",
        query_type="diagnosis_codes",
        query_definition={"fields": ["code"]},
        tenant_id=TENANT,
    )
    sq2 = register_query(
        db=db,
        qualified_name="billing::test",
        version="2.0.0",
        query_type="diagnosis_codes",
        query_definition={"fields": ["code", "desc"]},
        tenant_id=TENANT,
    )
    assert sq1.id != sq2.id
    assert sq1.version == "1.0.0"
    assert sq2.version == "2.0.0"


def test_get_query_returns_none_for_missing(db):
    result = get_query(db, "billing::nonexistent", "1.0.0", TENANT)
    assert result is None


def test_list_queries_empty(db):
    result = list_queries(db, TENANT)
    assert result == []


def test_list_queries_returns_all(db):
    register_query(db=db, qualified_name="q1", version="1.0.0",
                   query_type="diagnosis_codes",
                   query_definition={}, tenant_id=TENANT)
    register_query(db=db, qualified_name="q2", version="1.0.0",
                   query_type="procedure_codes",
                   query_definition={}, tenant_id=TENANT)
    result = list_queries(db, TENANT)
    assert len(result) == 2


def test_list_queries_respects_tenant(db):
    register_query(db=db, qualified_name="q1", version="1.0.0",
                   query_type="diagnosis_codes",
                   query_definition={}, tenant_id=TENANT)
    register_query(db=db, qualified_name="q2", version="1.0.0",
                   query_type="diagnosis_codes",
                   query_definition={}, tenant_id="other_tenant")
    result = list_queries(db, TENANT)
    assert len(result) == 1
    assert result[0].qualified_name == "q1"


def test_delete_query_removes_entry(db):
    register_query(db=db, qualified_name="billing::del", version="1.0.0",
                   query_type="diagnosis_codes",
                   query_definition={}, tenant_id=TENANT)
    assert delete_query(db, "billing::del", "1.0.0", TENANT) is True
    assert get_query(db, "billing::del", "1.0.0", TENANT) is None


def test_delete_query_returns_false_for_missing(db):
    assert delete_query(db, "billing::missing", "1.0.0", TENANT) is False


# =============================================================================
# Seed Tests
# =============================================================================

def test_seed_billing_queries_registers_four(db):
    registered = seed_billing_queries(db, TENANT)
    assert len(registered) == 4
    names = {sq.qualified_name for sq in registered}
    assert names == {
        "billing::diagnosis-codes",
        "billing::procedure-codes",
        "billing::encounter-summary",
        "billing::patient-coverage",
    }


def test_seed_billing_queries_idempotent(db):
    first = seed_billing_queries(db, TENANT)
    second = seed_billing_queries(db, TENANT)
    assert len(second) == 4
    for a, b in zip(first, second):
        assert a.id == b.id


# =============================================================================
# Execution Tests
# =============================================================================

def _seed_trade_data(db):
    """Insert test accounts, trades, positions, and account users."""
    account = Account(id=1, display_name="Test Account", tenant_id=TENANT)
    db.add(account)
    db.flush()

    trades = [
        Trade(account_id=1, security="AAPL", side="Buy", quantity=50,
              state="New", tenant_id=TENANT,
              created=datetime(2025, 1, 15), updated=datetime(2025, 1, 15)),
        Trade(account_id=1, security="MSFT", side="Sell", quantity=200,
              state="Settled", tenant_id=TENANT,
              created=datetime(2025, 2, 10), updated=datetime(2025, 2, 11)),
        Trade(account_id=1, security="GOOG", side="Buy", quantity=100,
              state="Processing", tenant_id=TENANT,
              created=datetime(2025, 3, 5), updated=datetime(2025, 3, 5)),
    ]
    db.add_all(trades)

    position = Position(account_id=1, security="AAPL", quantity=50,
                        tenant_id=TENANT)
    db.add(position)

    account_user = AccountUser(account_id=1, username="jdoe",
                               tenant_id=TENANT)
    db.add(account_user)
    db.commit()


def test_execute_diagnosis_codes(db):
    _seed_trade_data(db)
    seed_billing_queries(db, TENANT)

    result = execute_query(db, "billing::diagnosis-codes", "1.0.0", TENANT)
    assert result["queryName"] == "billing::diagnosis-codes"
    assert result["resultCount"] == 3
    codes = {r["diagnosisCode"] for r in result["results"]}
    assert "Z00.00" in codes  # New state
    assert "Z09" in codes     # Settled state


def test_execute_diagnosis_codes_with_date_filter(db):
    _seed_trade_data(db)
    seed_billing_queries(db, TENANT)

    result = execute_query(
        db, "billing::diagnosis-codes", "1.0.0", TENANT,
        parameters={"date_from": "2025-02-01", "date_to": "2025-02-28"},
    )
    assert result["resultCount"] == 1
    assert result["results"][0]["diagnosisCode"] == "Z09"


def test_execute_diagnosis_codes_with_patient_filter(db):
    _seed_trade_data(db)
    seed_billing_queries(db, TENANT)

    result = execute_query(
        db, "billing::diagnosis-codes", "1.0.0", TENANT,
        parameters={"patient_id": 1},
    )
    assert result["resultCount"] == 3

    result_empty = execute_query(
        db, "billing::diagnosis-codes", "1.0.0", TENANT,
        parameters={"patient_id": 999},
    )
    assert result_empty["resultCount"] == 0


def test_execute_procedure_codes(db):
    _seed_trade_data(db)
    seed_billing_queries(db, TENANT)

    result = execute_query(db, "billing::procedure-codes", "1.0.0", TENANT)
    assert result["resultCount"] == 3
    codes = {r["procedureCode"] for r in result["results"]}
    assert "99201" in codes  # Buy/New
    assert "99214" in codes  # Sell/Settled


def test_execute_encounter_summary(db):
    _seed_trade_data(db)
    seed_billing_queries(db, TENANT)

    result = execute_query(db, "billing::encounter-summary", "1.0.0", TENANT)
    assert result["resultCount"] == 1
    encounter = result["results"][0]
    assert encounter["accountId"] == 1
    assert encounter["totalProcedures"] == 3
    assert encounter["settledProcedures"] == 1
    assert encounter["encounterType"] == "outpatient"


def test_execute_patient_coverage(db):
    _seed_trade_data(db)
    seed_billing_queries(db, TENANT)

    result = execute_query(db, "billing::patient-coverage", "1.0.0", TENANT)
    assert result["resultCount"] == 1
    coverage = result["results"][0]
    assert coverage["username"] == "jdoe"
    assert coverage["accountId"] == 1
    assert coverage["activePositions"] == 1


def test_execute_query_not_found(db):
    with pytest.raises(QueryNotFoundError):
        execute_query(db, "billing::missing", "1.0.0", TENANT)


def test_execute_query_unsupported_type(db):
    register_query(
        db=db,
        qualified_name="billing::bad",
        version="1.0.0",
        query_type="nonexistent_handler",
        query_definition={},
        tenant_id=TENANT,
    )
    with pytest.raises(UnsupportedQueryTypeError):
        execute_query(db, "billing::bad", "1.0.0", TENANT)


def test_to_dict_serialization(db):
    sq = register_query(
        db=db,
        qualified_name="billing::ser",
        version="1.0.0",
        query_type="diagnosis_codes",
        query_definition={"fields": ["code"]},
        tenant_id=TENANT,
        description="Serialization test",
        parameters_schema={"type": "object"},
    )
    d = sq.to_dict()
    assert d["qualifiedName"] == "billing::ser"
    assert d["version"] == "1.0.0"
    assert d["queryDefinition"] == {"fields": ["code"]}
    assert d["parametersSchema"] == {"type": "object"}
    assert d["createdAt"] is not None
