"""
FHIR Billing code validation endpoints.

Provides REST API for validating coded entries against billing code systems
(ICD-10, CPT, HCPCS, SNOMED CT) using configurable FHIR terminology server
endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import billing_code_validator

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class CodedEntry(BaseModel):
    code: str
    system: str
    display: Optional[str] = None


class ValidateCodeRequest(BaseModel):
    code: str
    system: str


class CompositionValidateRequest(BaseModel):
    profile_id: str
    coded_entries: list[CodedEntry]
    server_url: Optional[str] = None


class BatchValidateRequest(BaseModel):
    profile_id: str
    coded_entries: list[CodedEntry]
    server_url: Optional[str] = None


# =============================================================================
# Billing Validation Endpoints
# =============================================================================

@router.get("/billing/profiles")
def list_profiles():
    """List all available billing validation profiles."""
    return billing_code_validator.get_available_profiles()


@router.get("/billing/profiles/{profile_id}")
def get_profile(profile_id: str):
    """Get a specific billing validation profile by ID."""
    profile = billing_code_validator.get_profile(profile_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Billing profile '{profile_id}' not found",
        )
    return {
        "id": profile_id,
        "name": profile["name"],
        "description": profile["description"],
        "required_code_systems": profile["required_code_systems"],
        "optional_code_systems": profile["optional_code_systems"],
    }


@router.post("/billing/validate-code")
def validate_single_code(body: ValidateCodeRequest):
    """Validate a single billing code against the FHIR terminology server."""
    is_valid, message = billing_code_validator.validate_coded_entry(
        code=body.code,
        system_name=body.system,
    )
    return {
        "valid": is_valid,
        "code": body.code,
        "system": body.system,
        "message": message,
    }


@router.post("/billing/validate-composition")
def validate_composition(body: CompositionValidateRequest):
    """
    Validate a composition's coded entries against a billing profile.

    Cross-references the coded entries against required billing code systems
    for the specified profile. Returns structured errors for any codes that
    fail validation.
    """
    entries = [e.model_dump() for e in body.coded_entries]
    result = billing_code_validator.validate_composition(
        coded_entries=entries,
        profile_id=body.profile_id,
        server_url=body.server_url,
    )
    return result.to_dict()


@router.post("/billing/batch-validate")
def batch_validate(body: BatchValidateRequest):
    """
    Batch-validate multiple coded entries against a billing profile in a
    single pass. This is the primary endpoint for billing validation.
    """
    entries = [e.model_dump() for e in body.coded_entries]
    result = billing_code_validator.batch_validate(
        coded_entries=entries,
        profile_id=body.profile_id,
        server_url=body.server_url,
    )
    return result.to_dict()
