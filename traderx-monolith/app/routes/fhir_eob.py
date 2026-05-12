"""
FHIR R4 ExplanationOfBenefit endpoints.
Provides a read-only FHIR R4-compliant REST interface for querying
trade data as ExplanationOfBenefit resources.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.services.eob_mapping_service import get_eobs_for_patient
from app.utils.helpers import get_tenant_from_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fhir/r4", tags=["FHIR R4"])

FHIR_MEDIA_TYPE = "application/fhir+json"


@router.get("/ExplanationOfBenefit")
def search_eob(
    request: Request,
    patient: int = Query(..., description="Patient (account) ID to search EOBs for"),
    _offset: int = Query(0, alias="_offset", ge=0, description="Pagination offset"),
    _count: int = Query(10, alias="_count", ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
):
    """
    Search ExplanationOfBenefit resources by patient.
    Returns a FHIR R4 Bundle with pagination links.
    """
    tenant_id = get_tenant_from_request(request)
    base_url = str(request.base_url).rstrip("/")

    bundle = get_eobs_for_patient(
        db=db,
        patient_id=patient,
        tenant_id=tenant_id,
        base_url=base_url,
        offset=_offset,
        count=_count,
    )

    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient} not found or access denied",
        )

    return JSONResponse(
        content=bundle.model_dump(mode="json"),
        media_type=FHIR_MEDIA_TYPE,
    )
