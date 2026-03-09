"""People endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.services import people_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/people/GetPerson")
def get_person(LogonId: str = Query(...)):
    person = people_service.get_person(LogonId)
    if person is None:
        raise HTTPException(status_code=404, detail=f"Person {LogonId} not found")
    return person.to_dict()


@router.get("/people/GetMatchingPeople")
def get_matching_people(SearchText: str = Query(...)):
    matches = people_service.get_matching_people(SearchText)
    return [p.to_dict() for p in matches]


@router.get("/people/ValidatePerson")
def validate_person(LogonId: str = Query(...)):
    is_valid = people_service.validate_person(LogonId)
    return {"IsValid": is_valid, "LogonId": LogonId}
