"""
FHIR Billing Code Validator service.

Validates coded entries against required billing code systems (ICD-10, CPT,
HCPCS, SNOMED CT) using configurable FHIR terminology server endpoints.
Supports batch validation and profile-based validation rules.
"""

import logging
from typing import Optional

import httpx

from app.config import (
    BILLING_CODE_SYSTEMS,
    BILLING_PROFILES,
    FHIR_ALLOW_SERVER_URL_OVERRIDE,
    FHIR_TERMINOLOGY_SERVER_URL,
    FHIR_VALIDATION_TIMEOUT,
)

logger = logging.getLogger(__name__)


class ValidationError:
    """Structured error for a single code validation failure."""

    def __init__(self, code: str, system: str, system_name: str, message: str):
        self.code = code
        self.system = system
        self.system_name = system_name
        self.message = message

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "system": self.system,
            "system_name": self.system_name,
            "message": self.message,
        }


class ValidationResult:
    """Aggregated validation result for a batch of coded entries."""

    def __init__(self):
        self.valid = True
        self.errors: list[ValidationError] = []
        self.validated_count = 0
        self.valid_count = 0

    def add_error(self, error: ValidationError):
        self.valid = False
        self.errors.append(error)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "validated_count": self.validated_count,
            "valid_count": self.valid_count,
            "error_count": len(self.errors),
            "errors": [e.to_dict() for e in self.errors],
        }


def get_available_profiles() -> list[dict]:
    """Return all configured billing profiles."""
    profiles = []
    for profile_id, profile in BILLING_PROFILES.items():
        profiles.append({
            "id": profile_id,
            "name": profile["name"],
            "description": profile["description"],
            "required_code_systems": profile["required_code_systems"],
            "optional_code_systems": profile["optional_code_systems"],
        })
    return profiles


def get_profile(profile_id: str) -> Optional[dict]:
    """Return a single billing profile by ID, or None if not found."""
    return BILLING_PROFILES.get(profile_id)


def _resolve_system_url(system_name: str) -> Optional[str]:
    """Resolve a billing code system name to its canonical FHIR URL."""
    return BILLING_CODE_SYSTEMS.get(system_name)


def _validate_code_against_server(
    code: str,
    system_url: str,
    server_url: str,
) -> tuple[bool, str]:
    """
    Validate a single code against a FHIR terminology server using the
    $validate-code operation.

    Returns (is_valid, message).
    """
    params = {
        "url": system_url,
        "code": code,
    }
    try:
        response = httpx.get(
            f"{server_url}/ValueSet/$validate-code",
            params=params,
            timeout=FHIR_VALIDATION_TIMEOUT,
        )
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                return False, "Terminology server returned invalid JSON"
            for param in data.get("parameter", []):
                if param.get("name") == "result":
                    return param.get("valueBoolean", False), "Valid"
            return False, "Unexpected response format from terminology server"
        return False, f"Terminology server returned status {response.status_code}"
    except httpx.TimeoutException:
        return False, "Terminology server request timed out"
    except httpx.RequestError as exc:
        return False, f"Terminology server connection error: {exc}"


def _resolve_server_url(server_url: Optional[str]) -> str:
    """Resolve the FHIR server URL, ignoring overrides when not allowed."""
    if server_url is not None and FHIR_ALLOW_SERVER_URL_OVERRIDE:
        return server_url
    return FHIR_TERMINOLOGY_SERVER_URL


def validate_coded_entry(
    code: str,
    system_name: str,
    server_url: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Validate a single coded entry against the FHIR terminology server.

    Args:
        code: The billing code to validate (e.g., "A01.0", "99213").
        system_name: The code system name (e.g., "ICD-10", "CPT").
        server_url: Optional override for the FHIR terminology server URL.
            Only used when FHIR_ALLOW_SERVER_URL_OVERRIDE is True.

    Returns:
        Tuple of (is_valid, message).
    """
    server_url = _resolve_server_url(server_url)

    system_url = _resolve_system_url(system_name)
    if system_url is None:
        return False, f"Unknown code system: {system_name}"

    return _validate_code_against_server(code, system_url, server_url)


def validate_composition(
    coded_entries: list[dict],
    profile_id: str,
    server_url: Optional[str] = None,
) -> ValidationResult:
    """
    Validate a composition's coded entries against a billing profile.

    Cross-references the composition's coded entries against the required
    billing code systems defined in the profile.

    Args:
        coded_entries: List of dicts with keys "code", "system", and
            optionally "display".
        profile_id: The billing profile ID to validate against.
        server_url: Optional override for the FHIR terminology server URL.

    Returns:
        ValidationResult with aggregated pass/fail and error details.
    """
    server_url = _resolve_server_url(server_url)

    result = ValidationResult()

    profile = get_profile(profile_id)
    if profile is None:
        error = ValidationError(
            code="",
            system="",
            system_name="",
            message=f"Unknown billing profile: {profile_id}",
        )
        result.add_error(error)
        return result

    required_systems = set(profile["required_code_systems"])
    all_known_systems = required_systems | set(profile["optional_code_systems"])
    systems_present: dict[str, list[dict]] = {}

    for entry in coded_entries:
        system_name = entry.get("system", "")
        if system_name in all_known_systems:
            systems_present.setdefault(system_name, []).append(entry)

    for required in required_systems:
        if required not in systems_present:
            system_url = _resolve_system_url(required) or required
            error = ValidationError(
                code="",
                system=system_url,
                system_name=required,
                message=f"Required code system '{required}' not present in composition",
            )
            result.add_error(error)

    for entry in coded_entries:
        code = entry.get("code", "")
        system_name = entry.get("system", "")

        if system_name not in all_known_systems:
            continue

        result.validated_count += 1
        is_valid, message = validate_coded_entry(code, system_name, server_url)
        if is_valid:
            result.valid_count += 1
        else:
            system_url = _resolve_system_url(system_name) or system_name
            error = ValidationError(
                code=code,
                system=system_url,
                system_name=system_name,
                message=message,
            )
            result.add_error(error)

    logger.info(
        "Billing validation for profile '%s': %d/%d codes valid",
        profile_id,
        result.valid_count,
        result.validated_count,
    )
    return result


def batch_validate(
    coded_entries: list[dict],
    profile_id: str,
    server_url: Optional[str] = None,
) -> ValidationResult:
    """
    Batch-validate multiple coded entries against a billing profile in a
    single pass. This is the primary entry point for billing validation.

    Args:
        coded_entries: List of dicts with keys "code", "system", and
            optionally "display".
        profile_id: The billing profile ID to validate against.
        server_url: Optional override for the FHIR terminology server URL.

    Returns:
        ValidationResult with aggregated results for the entire batch.
    """
    return validate_composition(coded_entries, profile_id, server_url)
