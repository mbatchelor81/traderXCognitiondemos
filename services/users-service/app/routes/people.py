"""People endpoints for Users Service."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services import people_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/people/GetPerson")
def get_person(LogonId: Optional[str] = Query(None),
               EmployeeId: Optional[str] = Query(None)):
    """Get a person by LogonId or EmployeeId."""
    if not LogonId and not EmployeeId:
        raise HTTPException(
            status_code=400,
            detail="Either LogonId or EmployeeId must be provided"
        )

    person = people_service.get_person(logon_id=LogonId, employee_id=EmployeeId)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return person.to_dict()


@router.get("/people/GetMatchingPeople")
def get_matching_people(SearchText: Optional[str] = Query(None),
                        Take: int = Query(10)):
    """Search for people matching search text."""
    if not SearchText:
        raise HTTPException(
            status_code=400,
            detail="SearchText must be provided"
        )

    if len(SearchText) < 3:
        raise HTTPException(
            status_code=400,
            detail="SearchText must be at least 3 characters long"
        )

    people = people_service.get_matching_people(SearchText, Take)
    if not people:
        return {"People": []}

    return {"People": [p.to_dict() for p in people]}


@router.get("/people/ValidatePerson")
def validate_person_endpoint(LogonId: Optional[str] = Query(None),
                             EmployeeId: Optional[str] = Query(None)):
    """Validate that a person exists."""
    if not LogonId and not EmployeeId:
        raise HTTPException(
            status_code=400,
            detail="Either LogonId or EmployeeId must be provided"
        )

    is_valid = people_service.validate_person(
        logon_id=LogonId, employee_id=EmployeeId
    )

    return {"IsValid": is_valid}
