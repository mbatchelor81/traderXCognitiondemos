"""
Integration tests for FHIR billing validation endpoints with a mock
FHIR terminology server.

Uses a real HTTP server (via threading) to simulate the FHIR terminology
server responses, then exercises the FastAPI endpoints end-to-end.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import pytest


# =============================================================================
# Mock FHIR Terminology Server
# =============================================================================

VALID_CODES = {
    "http://hl7.org/fhir/sid/icd-10-cm": {"A01.0", "J06.9", "E11.9"},
    "http://www.ama-assn.org/go/cpt": {"99213", "99214", "99215"},
    "https://www.cms.gov/Medicare/Coding/HCPCSReleaseCodeSets": {"G0101", "G0102"},
    "http://snomed.info/sct": {"386661006", "73211009"},
}


class MockFHIRHandler(BaseHTTPRequestHandler):
    """Handles FHIR $validate-code requests with a static code registry."""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/ValueSet/$validate-code":
            params = parse_qs(parsed.query)
            system_url = params.get("url", [""])[0]
            code = params.get("code", [""])[0]

            valid_set = VALID_CODES.get(system_url, set())
            is_valid = code in valid_set

            body = {
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "result", "valueBoolean": is_valid},
                ],
            }
            payload = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/fhir+json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def mock_fhir_server():
    """Start a mock FHIR terminology server on a random port."""
    server = HTTPServer(("127.0.0.1", 0), MockFHIRHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


# =============================================================================
# Integration Tests — Profile endpoints
# =============================================================================

def test_list_profiles_endpoint(client):
    resp = client.get("/billing/profiles")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    ids = [p["id"] for p in data]
    assert "us-claims" in ids


def test_get_profile_endpoint(client):
    resp = client.get("/billing/profiles/us-claims")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "us-claims"
    assert "ICD-10" in data["required_code_systems"]


def test_get_profile_not_found(client):
    resp = client.get("/billing/profiles/nonexistent")
    assert resp.status_code == 404


# =============================================================================
# Integration Tests — Single code validation with mock server
# =============================================================================

def test_validate_single_icd10_valid(client, mock_fhir_server):
    resp = client.post("/billing/validate-code", json={
        "code": "A01.0",
        "system": "ICD-10",
    })
    assert resp.status_code == 200


def test_validate_single_cpt_valid(client, mock_fhir_server):
    resp = client.post("/billing/validate-code", json={
        "code": "99213",
        "system": "CPT",
    })
    assert resp.status_code == 200


def test_validate_single_unknown_system(client):
    resp = client.post("/billing/validate-code", json={
        "code": "12345",
        "system": "UNKNOWN",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert "Unknown code system" in data["message"]


# =============================================================================
# Integration Tests — Composition validation with mock server
# =============================================================================

def test_validate_composition_all_valid(client, mock_fhir_server):
    resp = client.post("/billing/validate-composition", json={
        "profile_id": "us-claims",
        "coded_entries": [
            {"code": "A01.0", "system": "ICD-10", "display": "Typhoid fever"},
            {"code": "99213", "system": "CPT", "display": "Office visit"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["validated_count"] == 2
    assert data["valid_count"] == 2
    assert data["error_count"] == 0


def test_validate_composition_invalid_code(client, mock_fhir_server):
    resp = client.post("/billing/validate-composition", json={
        "profile_id": "us-claims",
        "coded_entries": [
            {"code": "INVALID_ICD", "system": "ICD-10"},
            {"code": "99213", "system": "CPT"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["error_count"] >= 1
    invalid_errors = [e for e in data["errors"] if e["code"] == "INVALID_ICD"]
    assert len(invalid_errors) == 1


def test_validate_composition_missing_required_system(client, mock_fhir_server):
    resp = client.post("/billing/validate-composition", json={
        "profile_id": "us-claims",
        "coded_entries": [
            {"code": "A01.0", "system": "ICD-10"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    missing_errors = [e for e in data["errors"] if "not present" in e["message"]]
    assert len(missing_errors) >= 1


def test_validate_composition_unknown_profile(client, mock_fhir_server):
    resp = client.post("/billing/validate-composition", json={
        "profile_id": "nonexistent",
        "coded_entries": [
            {"code": "A01.0", "system": "ICD-10"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert any("Unknown billing profile" in e["message"] for e in data["errors"])


# =============================================================================
# Integration Tests — Batch validation with mock server
# =============================================================================

def test_batch_validate_multiple_systems(client, mock_fhir_server):
    resp = client.post("/billing/batch-validate", json={
        "profile_id": "us-professional",
        "coded_entries": [
            {"code": "E11.9", "system": "ICD-10", "display": "Type 2 diabetes"},
            {"code": "99214", "system": "CPT", "display": "Office visit level 4"},
            {"code": "G0101", "system": "HCPCS", "display": "Cervical screening"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["validated_count"] == 3
    assert data["valid_count"] == 3


def test_batch_validate_with_snomed(client, mock_fhir_server):
    resp = client.post("/billing/batch-validate", json={
        "profile_id": "clinical-coding",
        "coded_entries": [
            {"code": "386661006", "system": "SNOMED-CT", "display": "Fever"},
            {"code": "J06.9", "system": "ICD-10", "display": "Acute URI"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["validated_count"] == 2


def test_batch_validate_mixed_valid_invalid(client, mock_fhir_server):
    resp = client.post("/billing/batch-validate", json={
        "profile_id": "us-claims",
        "coded_entries": [
            {"code": "A01.0", "system": "ICD-10"},
            {"code": "BADCPT", "system": "CPT"},
        ],
        "server_url": mock_fhir_server,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["validated_count"] == 2
    assert data["valid_count"] == 1
    assert data["error_count"] >= 1


def test_existing_non_billing_endpoints_unaffected(client):
    """Billing validation does not break existing flows."""
    resp = client.get("/account/")
    assert resp.status_code == 200

    resp = client.get("/health")
    assert resp.status_code == 200
