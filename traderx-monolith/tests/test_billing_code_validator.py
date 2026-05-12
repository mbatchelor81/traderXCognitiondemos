"""Unit tests for FHIR billing code validation service."""

from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.services.billing_code_validator import (
    ValidationError,
    ValidationResult,
    _resolve_server_url,
    batch_validate,
    get_available_profiles,
    get_profile,
    validate_coded_entry,
    validate_composition,
)


# =============================================================================
# Profile configuration tests
# =============================================================================

def test_get_available_profiles_returns_all():
    profiles = get_available_profiles()
    profile_ids = [p["id"] for p in profiles]
    assert "us-claims" in profile_ids
    assert "us-professional" in profile_ids
    assert "clinical-coding" in profile_ids


def test_get_available_profiles_structure():
    profiles = get_available_profiles()
    for profile in profiles:
        assert "id" in profile
        assert "name" in profile
        assert "description" in profile
        assert "required_code_systems" in profile
        assert "optional_code_systems" in profile


def test_get_profile_existing():
    profile = get_profile("us-claims")
    assert profile is not None
    assert profile["name"] == "US Claims"
    assert "ICD-10" in profile["required_code_systems"]
    assert "CPT" in profile["required_code_systems"]


def test_get_profile_nonexistent():
    assert get_profile("nonexistent") is None


# =============================================================================
# Single code validation tests
# =============================================================================

def _mock_fhir_response(valid: bool):
    """Build a mock FHIR $validate-code response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": valid},
        ],
    }
    return resp


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_icd10_code_valid(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    is_valid, message = validate_coded_entry("A01.0", "ICD-10")
    assert is_valid is True
    assert message == "Valid"
    call_args = mock_get.call_args
    assert "icd-10" in call_args.kwargs["params"]["url"].lower() or \
           "icd-10" in call_args.args[0].lower() or \
           "icd-10-cm" in call_args.kwargs["params"]["url"]


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_icd10_code_invalid(mock_get):
    mock_get.return_value = _mock_fhir_response(False)
    is_valid, message = validate_coded_entry("INVALID", "ICD-10")
    assert is_valid is False
    assert "not found" in message.lower()


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_cpt_code_valid(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    is_valid, message = validate_coded_entry("99213", "CPT")
    assert is_valid is True
    call_args = mock_get.call_args
    assert "cpt" in call_args.kwargs["params"]["url"].lower()


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_cpt_code_invalid(mock_get):
    mock_get.return_value = _mock_fhir_response(False)
    is_valid, message = validate_coded_entry("00000", "CPT")
    assert is_valid is False
    assert "not found" in message.lower()


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_snomed_code_valid(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    is_valid, message = validate_coded_entry("386661006", "SNOMED-CT")
    assert is_valid is True
    call_args = mock_get.call_args
    assert "snomed" in call_args.kwargs["params"]["url"].lower()


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_snomed_code_invalid(mock_get):
    mock_get.return_value = _mock_fhir_response(False)
    is_valid, message = validate_coded_entry("0000000", "SNOMED-CT")
    assert is_valid is False
    assert "not found" in message.lower()


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_hcpcs_code_valid(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    is_valid, message = validate_coded_entry("G0101", "HCPCS")
    assert is_valid is True


def test_validate_unknown_code_system():
    is_valid, message = validate_coded_entry("12345", "UNKNOWN-SYSTEM")
    assert is_valid is False
    assert "Unknown code system" in message


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_code_server_timeout(mock_get):
    mock_get.side_effect = httpx.TimeoutException("timeout")
    is_valid, message = validate_coded_entry("A01.0", "ICD-10")
    assert is_valid is False
    assert "timed out" in message


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_code_server_error(mock_get):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 500
    mock_get.return_value = resp
    is_valid, message = validate_coded_entry("A01.0", "ICD-10")
    assert is_valid is False
    assert "500" in message


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_code_connection_error(mock_get):
    mock_get.side_effect = httpx.ConnectError("connection refused")
    is_valid, message = validate_coded_entry("A01.0", "ICD-10")
    assert is_valid is False
    assert "connection error" in message.lower()


# =============================================================================
# Composition validation tests
# =============================================================================

@patch("app.services.billing_code_validator.httpx.get")
def test_validate_composition_us_claims_valid(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    entries = [
        {"code": "A01.0", "system": "ICD-10", "display": "Typhoid fever"},
        {"code": "99213", "system": "CPT", "display": "Office visit"},
    ]
    result = validate_composition(entries, "us-claims")
    assert result.valid is True
    assert result.validated_count == 2
    assert result.valid_count == 2
    assert len(result.errors) == 0


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_composition_missing_required_system(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    entries = [
        {"code": "A01.0", "system": "ICD-10", "display": "Typhoid fever"},
    ]
    result = validate_composition(entries, "us-claims")
    assert result.valid is False
    errors_dict = result.to_dict()["errors"]
    missing_cpt = [e for e in errors_dict if e["system_name"] == "CPT"]
    assert len(missing_cpt) == 1
    assert "not present" in missing_cpt[0]["message"]


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_composition_invalid_code(mock_get):
    def side_effect(*args, **kwargs):
        code = kwargs.get("params", {}).get("code", "")
        if code == "INVALID":
            return _mock_fhir_response(False)
        return _mock_fhir_response(True)

    mock_get.side_effect = side_effect
    entries = [
        {"code": "INVALID", "system": "ICD-10"},
        {"code": "99213", "system": "CPT"},
    ]
    result = validate_composition(entries, "us-claims")
    assert result.valid is False
    assert result.validated_count == 2
    assert result.valid_count == 1
    errors_dict = result.to_dict()["errors"]
    assert any(e["code"] == "INVALID" for e in errors_dict)


def test_validate_composition_unknown_profile():
    result = validate_composition([], "nonexistent-profile")
    assert result.valid is False
    assert len(result.errors) == 1
    assert "Unknown billing profile" in result.errors[0].message


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_composition_ignores_unrelated_systems(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    entries = [
        {"code": "A01.0", "system": "ICD-10"},
        {"code": "99213", "system": "CPT"},
        {"code": "XYZ", "system": "SOME-OTHER-SYSTEM"},
    ]
    result = validate_composition(entries, "us-claims")
    assert result.validated_count == 2


@patch("app.services.billing_code_validator.httpx.get")
def test_validate_composition_optional_system_validated(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    entries = [
        {"code": "A01.0", "system": "ICD-10"},
        {"code": "99213", "system": "CPT"},
        {"code": "386661006", "system": "SNOMED-CT"},
    ]
    result = validate_composition(entries, "us-claims")
    assert result.valid is True
    assert result.validated_count == 3
    assert result.valid_count == 3


# =============================================================================
# Batch validation tests
# =============================================================================

@patch("app.services.billing_code_validator.httpx.get")
def test_batch_validate_delegates_to_composition(mock_get):
    mock_get.return_value = _mock_fhir_response(True)
    entries = [
        {"code": "A01.0", "system": "ICD-10"},
        {"code": "99213", "system": "CPT"},
    ]
    result = batch_validate(entries, "us-claims")
    assert result.valid is True
    assert result.validated_count == 2


# =============================================================================
# ValidationResult / ValidationError model tests
# =============================================================================

def test_validation_result_to_dict():
    result = ValidationResult()
    result.validated_count = 2
    result.valid_count = 1
    error = ValidationError(
        code="BAD",
        system="http://example.com",
        system_name="TEST",
        message="Invalid code",
    )
    result.add_error(error)
    d = result.to_dict()
    assert d["valid"] is False
    assert d["validated_count"] == 2
    assert d["valid_count"] == 1
    assert d["error_count"] == 1
    assert d["errors"][0]["code"] == "BAD"


def test_validation_error_to_dict():
    error = ValidationError(
        code="A01.0",
        system="http://hl7.org/fhir/sid/icd-10-cm",
        system_name="ICD-10",
        message="Valid",
    )
    d = error.to_dict()
    assert d["code"] == "A01.0"
    assert d["system"] == "http://hl7.org/fhir/sid/icd-10-cm"
    assert d["system_name"] == "ICD-10"
    assert d["message"] == "Valid"


# =============================================================================
# Invalid JSON response handling tests
# =============================================================================

@patch("app.services.billing_code_validator.httpx.get")
def test_validate_code_invalid_json_response(mock_get):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.side_effect = ValueError("No JSON")
    mock_get.return_value = resp
    is_valid, message = validate_coded_entry("A01.0", "ICD-10")
    assert is_valid is False
    assert "invalid JSON" in message


# =============================================================================
# SSRF protection tests
# =============================================================================

def test_resolve_server_url_override_disabled():
    """When override is disabled, custom server_url is ignored."""
    with patch(
        "app.services.billing_code_validator.FHIR_ALLOW_SERVER_URL_OVERRIDE", False
    ):
        result = _resolve_server_url("http://evil.internal:8080")
        assert result != "http://evil.internal:8080"


def test_resolve_server_url_override_enabled():
    """When override is enabled, custom server_url is used."""
    with patch(
        "app.services.billing_code_validator.FHIR_ALLOW_SERVER_URL_OVERRIDE", True
    ):
        result = _resolve_server_url("http://custom-server:9999")
        assert result == "http://custom-server:9999"


def test_resolve_server_url_none_always_uses_default():
    """When server_url is None, always use the configured default."""
    with patch(
        "app.services.billing_code_validator.FHIR_ALLOW_SERVER_URL_OVERRIDE", True
    ):
        from app.config import FHIR_TERMINOLOGY_SERVER_URL
        result = _resolve_server_url(None)
        assert result == FHIR_TERMINOLOGY_SERVER_URL
