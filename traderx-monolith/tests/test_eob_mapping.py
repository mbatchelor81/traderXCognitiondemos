"""Unit tests for the EobMappingService mapping logic."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from app.services.eob_mapping_service import map_trade_to_eob


def _make_trade(**overrides):
    defaults = dict(
        id=1,
        tenant_id="acme_corp",
        account_id=100,
        security="AAPL",
        side="Buy",
        quantity=50,
        state="Settled",
        created=datetime(2025, 6, 1, 12, 0, 0),
        updated=datetime(2025, 6, 1, 12, 5, 0),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_account(**overrides):
    defaults = dict(id=100, tenant_id="acme_corp", display_name="Test Account")
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestMapTradeToEob:
    def test_resource_type_and_id(self):
        eob = map_trade_to_eob(_make_trade(), _make_account())
        assert eob.resourceType == "ExplanationOfBenefit"
        assert eob.id == "eob-trade-1"

    def test_patient_reference(self):
        eob = map_trade_to_eob(_make_trade(), _make_account())
        assert eob.patient.reference == "Patient/100"
        assert eob.patient.display == "Test Account"

    def test_insurer_reference_uses_tenant(self):
        eob = map_trade_to_eob(_make_trade(tenant_id="globex_inc"), _make_account())
        assert eob.insurer.reference == "Organization/globex_inc"

    def test_provider_reference(self):
        eob = map_trade_to_eob(_make_trade(), _make_account())
        assert eob.provider.reference == "Organization/traderx"

    def test_status_active_for_new_trade(self):
        eob = map_trade_to_eob(_make_trade(state="New"), _make_account())
        assert eob.status == "active"

    def test_status_active_for_processing_trade(self):
        eob = map_trade_to_eob(_make_trade(state="Processing"), _make_account())
        assert eob.status == "active"

    def test_status_complete_for_settled_trade(self):
        eob = map_trade_to_eob(_make_trade(state="Settled"), _make_account())
        assert eob.status == "complete"

    def test_outcome_complete_for_settled(self):
        eob = map_trade_to_eob(_make_trade(state="Settled"), _make_account())
        assert eob.outcome == "complete"

    def test_outcome_queued_for_new(self):
        eob = map_trade_to_eob(_make_trade(state="New"), _make_account())
        assert eob.outcome == "queued"

    def test_item_contains_security_and_quantity(self):
        eob = map_trade_to_eob(_make_trade(security="MSFT", quantity=200), _make_account())
        assert len(eob.item) == 1
        item = eob.item[0]
        assert item.sequence == 1
        assert item.productOrService.coding[0].code == "MSFT"
        assert item.quantity == {"value": 200, "unit": "shares"}

    def test_billable_period(self):
        eob = map_trade_to_eob(_make_trade(), _make_account())
        assert eob.billablePeriod is not None
        assert eob.billablePeriod.start == "2025-06-01T12:00:00"
        assert eob.billablePeriod.end == "2025-06-01T12:05:00"

    def test_identifier_contains_trade_id(self):
        eob = map_trade_to_eob(_make_trade(id=42), _make_account())
        assert eob.identifier[0].value == "42"
        assert "trade-id" in eob.identifier[0].system

    def test_insurance_coverage(self):
        eob = map_trade_to_eob(_make_trade(), _make_account())
        assert len(eob.insurance) == 1
        assert eob.insurance[0].focal is True
        assert "acme_corp" in eob.insurance[0].coverage.reference

    def test_total_reflects_quantity(self):
        eob = map_trade_to_eob(_make_trade(quantity=300), _make_account())
        assert len(eob.total) == 1
        assert eob.total[0].amount.value == 300.0
        assert eob.total[0].amount.currency == "USD"

    def test_account_display_name_fallback(self):
        eob = map_trade_to_eob(
            _make_trade(account_id=99),
            _make_account(id=99, display_name=None),
        )
        assert eob.patient.display == "Account 99"

    def test_status_cancelled_for_cancelled_trade(self):
        eob = map_trade_to_eob(_make_trade(state="Cancelled"), _make_account())
        assert eob.status == "cancelled"

    def test_outcome_error_for_cancelled_trade(self):
        eob = map_trade_to_eob(_make_trade(state="Cancelled"), _make_account())
        assert eob.outcome == "error"
