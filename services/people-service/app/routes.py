"""People Service route handlers."""
import logging
from fastapi import APIRouter, HTTPException, Query

from app.service import get_person, get_matching_people, validate_person

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/people/GetPerson")
def get_person_endpoint(LogonId: str = Query(...)):
    person = get_person(LogonId)
    if person is None:
        raise HTTPException(status_code=404, detail=f"Person {LogonId} not found")
    return person.model_dump()


@router.get("/people/GetMatchingPeople")
def get_matching_people_endpoint(SearchText: str = Query(...)):
    results = get_matching_people(SearchText)
    return [p.model_dump() for p in results]


@router.get("/people/ValidatePerson")
def validate_person_endpoint(LogonId: str = Query(...)):
    return validate_person(LogonId)
