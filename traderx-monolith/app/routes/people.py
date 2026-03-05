"""
People endpoints.
Ported from people-service .NET implementation (PeopleService.Core).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.services import people_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/people/GetPerson")
def get_person(LogonId: Optional[str] = Query(None),
               EmployeeId: Optional[str] = Query(None)):
    """
    Get a person by LogonId or EmployeeId.
    Mirrors PeopleService.Core.Queries.GetPerson.
    """
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
    """
    Search for people matching search text.
    Mirrors PeopleService.Core.Queries.GetMatchingPeople.
    """
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
        return None

    return {"People": [p.to_dict() for p in people]}


@router.get("/people/ValidatePerson")
def validate_person(LogonId: Optional[str] = Query(None),
                    EmployeeId: Optional[str] = Query(None)):
    """
    Validate that a person exists.
    Mirrors PeopleService.Core.Queries.ValidatePerson.
    """
    if not LogonId and not EmployeeId:
        raise HTTPException(
            status_code=400,
            detail="Either LogonId or EmployeeId must be provided"
        )

    is_valid = people_service.validate_person(
        logon_id=LogonId, employee_id=EmployeeId
    )

    return {"IsValid": is_valid}
