"""
People service — the person directory.

The directory is a static JSON file loaded exactly once into an immutable
tuple at startup; there is no database and no mutable global state.
"""

from __future__ import annotations

import json
from functools import lru_cache

from app.config import PEOPLE_DATA_FILE
from app.logging_config import get_logger
from app.models.person import Person

logger = get_logger(__name__)

MIN_SEARCH_TEXT_LENGTH = 3
DEFAULT_TAKE = 10


@lru_cache(maxsize=1)
def load_directory() -> tuple[Person, ...]:
    """Load the person directory once and return it as an immutable tuple."""
    try:
        with open(PEOPLE_DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        logger.error("people_data_file_missing", extra={"path": PEOPLE_DATA_FILE})
        return ()
    except Exception:
        logger.exception("people_data_load_failed", extra={"path": PEOPLE_DATA_FILE})
        return ()

    directory = tuple(Person.from_dict(p) for p in raw)
    logger.info(
        "people_directory_loaded",
        extra={"person_count": len(directory), "path": PEOPLE_DATA_FILE},
    )
    return directory


def get_person(
    tenant_id: str,
    logon_id: str | None = None,
    employee_id: str | None = None,
) -> Person | None:
    """Get a single person by LogonId, falling back to EmployeeId."""
    directory = load_directory()

    if logon_id:
        for person in directory:
            if person.logon_id == logon_id:
                return person

    if employee_id:
        for person in directory:
            if person.employee_id == employee_id:
                return person

    logger.info(
        "person_not_found",
        extra={"tenant_id": tenant_id, "logon_id": logon_id, "employee_id": employee_id},
    )
    return None


def get_matching_people(
    tenant_id: str,
    search_text: str,
    take: int = DEFAULT_TAKE,
) -> list[Person]:
    """Search people whose full name or logon id contains search_text."""
    if not search_text or len(search_text) < MIN_SEARCH_TEXT_LENGTH:
        return []

    search_lower = search_text.lower()
    results: list[Person] = []
    for person in load_directory():
        if (search_lower in person.full_name.lower()
                or search_lower in person.logon_id.lower()):
            results.append(person)
            if len(results) >= take:
                break

    logger.info(
        "people_searched",
        extra={"tenant_id": tenant_id, "search_text": search_text, "match_count": len(results)},
    )
    return results


def validate_person(
    tenant_id: str,
    logon_id: str | None = None,
    employee_id: str | None = None,
) -> bool:
    """Validate that a person exists in the directory."""
    return get_person(tenant_id, logon_id=logon_id, employee_id=employee_id) is not None


def get_all_people(tenant_id: str) -> list[Person]:
    """Return every person in the directory."""
    return list(load_directory())
