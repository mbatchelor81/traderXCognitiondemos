"""Integration tests for the FHIR R4 ExplanationOfBenefit endpoint."""

import pytest


FHIR_MEDIA_TYPE = "application/fhir+json"


# =============================================================================
# Helpers
# =============================================================================

def _create_account(client, name="Trading Account"):
    resp = client.post("/account/", json={"displayName": name})
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, account_id, security="AAPL", side="Buy", quantity=100):
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    return resp.json()


# =============================================================================
# Happy-Path Tests
# =============================================================================

class TestFhirEobEndpoint:
    def test_returns_fhir_json_content_type(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id)
        resp = client.get(f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}")
        assert resp.status_code == 200
        assert FHIR_MEDIA_TYPE in resp.headers["content-type"]

    def test_returns_bundle_resource_type(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id)
        resp = client.get(f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}")
        bundle = resp.json()
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"

    def test_bundle_total_matches_trade_count(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id, security="AAPL")
        _submit_trade(client, acct_id, security="MSFT")
        resp = client.get(f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}")
        bundle = resp.json()
        assert bundle["total"] == 2
        assert len(bundle["entry"]) == 2

    def test_eob_entry_structure(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id, security="GOOG", quantity=75)
        resp = client.get(f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}")
        bundle = resp.json()
        entry = bundle["entry"][0]
        eob = entry["resource"]
        assert eob["resourceType"] == "ExplanationOfBenefit"
        assert eob["patient"]["reference"] == f"Patient/{acct_id}"
        assert len(eob["item"]) == 1
        assert eob["item"][0]["productOrService"]["coding"][0]["code"] == "GOOG"
        assert eob["item"][0]["quantity"]["value"] == 75

    def test_empty_bundle_for_account_with_no_trades(self, client):
        acct_id = _create_account(client)
        resp = client.get(f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}")
        bundle = resp.json()
        assert bundle["total"] == 0
        assert bundle["entry"] == []


# =============================================================================
# Pagination Tests
# =============================================================================

class TestFhirEobPagination:
    def test_default_page_size(self, client):
        acct_id = _create_account(client)
        for i in range(15):
            _submit_trade(client, acct_id, security="AAPL", quantity=10 + i)
        resp = client.get(f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}")
        bundle = resp.json()
        assert bundle["total"] == 15
        assert len(bundle["entry"]) == 10

    def test_next_link_present_when_more_pages(self, client):
        acct_id = _create_account(client)
        for i in range(5):
            _submit_trade(client, acct_id, security="AAPL", quantity=10 + i)
        resp = client.get(
            f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}&_count=2"
        )
        bundle = resp.json()
        assert bundle["total"] == 5
        assert len(bundle["entry"]) == 2
        link_rels = {l["relation"]: l["url"] for l in bundle["link"]}
        assert "next" in link_rels
        assert "_offset=2" in link_rels["next"]

    def test_no_next_link_on_last_page(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id)
        resp = client.get(
            f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}&_count=10"
        )
        bundle = resp.json()
        link_rels = {l["relation"] for l in bundle["link"]}
        assert "next" not in link_rels

    def test_offset_skips_entries(self, client):
        acct_id = _create_account(client)
        for i in range(5):
            _submit_trade(client, acct_id, security="AAPL", quantity=10 + i)
        resp = client.get(
            f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}&_offset=3&_count=10"
        )
        bundle = resp.json()
        assert bundle["total"] == 5
        assert len(bundle["entry"]) == 2


# =============================================================================
# Access Control Tests
# =============================================================================

class TestFhirEobAccessControl:
    def test_patient_not_found_returns_404(self, client):
        resp = client.get("/fhir/r4/ExplanationOfBenefit?patient=99999")
        assert resp.status_code == 404

    def test_cross_tenant_access_denied(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id)
        resp = client.get(
            f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}",
            headers={"X-Tenant-ID": "other_tenant"},
        )
        assert resp.status_code == 404

    def test_missing_patient_param_returns_422(self, client):
        resp = client.get("/fhir/r4/ExplanationOfBenefit")
        assert resp.status_code == 422


# =============================================================================
# Multi-Tenant Isolation Tests
# =============================================================================

class TestFhirEobMultiTenant:
    def test_tenant_sees_only_own_trades(self, client):
        acct_id = _create_account(client)
        _submit_trade(client, acct_id)
        resp_default = client.get(
            f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}"
        )
        assert resp_default.status_code == 200
        assert resp_default.json()["total"] >= 1

        resp_other = client.get(
            f"/fhir/r4/ExplanationOfBenefit?patient={acct_id}",
            headers={"X-Tenant-ID": "globex_inc"},
        )
        assert resp_other.status_code == 404
