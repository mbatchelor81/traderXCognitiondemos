"""
People endpoints.

Paths, query parameter names and JSON keys are kept byte-identical to the
monolith — account-service calls ValidatePerson over HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.logging_config import get_logger
from app.services import people_service

logger = get_logger(__name__)

router = APIRouter()


class PersonResponse(BaseModel):
    """A person in the directory."""

    LogonId: str = Field(default="", description="Logon identifier")
    FullName: str = Field(default="", description="Full display name")
    Email: str = Field(default="", description="Email address")
    EmployeeId: str = Field(default="", description="Employee identifier")
    Department: str = Field(default="", description="Department name")
    PhotoUrl: str = Field(default="", description="Profile photo URL")


class MatchingPeopleResponse(BaseModel):
    """A list of people matching a search."""

    People: list[PersonResponse] = Field(default_factory=list)


class ValidatePersonResponse(BaseModel):
    """The result of a person existence check."""

    IsValid: bool


@router.get(
    "/people/GetPerson",
    response_model=PersonResponse,
    summary="Get a person by LogonId or EmployeeId",
)
def get_person(
    request: Request,
    LogonId: str | None = Query(None, description="Logon identifier"),
    EmployeeId: str | None = Query(None, description="Employee identifier"),
) -> PersonResponse:
    if not LogonId and not EmployeeId:
        raise HTTPException(
            status_code=400,
            detail="Either LogonId or EmployeeId must be provided",
        )

    person = people_service.get_person(
        request.state.tenant_id, logon_id=LogonId, employee_id=EmployeeId
    )
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return PersonResponse(**person.to_dict())


@router.get(
    "/people/GetMatchingPeople",
    response_model=MatchingPeopleResponse,
    summary="Search the person directory by name or logon id",
)
def get_matching_people(
    request: Request,
    SearchText: str | None = Query(None, description="At least 3 characters"),
    Take: int = Query(people_service.DEFAULT_TAKE, description="Maximum results to return"),
) -> MatchingPeopleResponse:
    if not SearchText:
        raise HTTPException(status_code=400, detail="SearchText must be provided")

    if len(SearchText) < people_service.MIN_SEARCH_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="SearchText must be at least 3 characters long",
        )

    people = people_service.get_matching_people(
        request.state.tenant_id, SearchText, Take
    )
    return MatchingPeopleResponse(
        People=[PersonResponse(**p.to_dict()) for p in people]
    )


@router.get(
    "/people/ValidatePerson",
    response_model=ValidatePersonResponse,
    summary="Validate that a person exists",
)
def validate_person(
    request: Request,
    LogonId: str | None = Query(None, description="Logon identifier"),
    EmployeeId: str | None = Query(None, description="Employee identifier"),
) -> ValidatePersonResponse:
    if not LogonId and not EmployeeId:
        raise HTTPException(
            status_code=400,
            detail="Either LogonId or EmployeeId must be provided",
        )

    is_valid = people_service.validate_person(
        request.state.tenant_id, logon_id=LogonId, employee_id=EmployeeId
    )
    return ValidatePersonResponse(IsValid=is_valid)
