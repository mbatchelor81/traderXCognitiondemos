"""People service - loads and queries JSON mock data."""

import json
import logging
import os
from typing import List, Optional

from app.config import PEOPLE_DATA_FILE
from app.models.person import Person

logger = logging.getLogger(__name__)

_people: Optional[List[Person]] = None


def _ensure_loaded():
    """Ensure people data is loaded into memory."""
    global _people
    if _people is None:
        people = []
        try:
            with open(PEOPLE_DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            _people = [Person.from_dict(p) for p in raw]
            logger.info("People service loaded %d people records", len(_people))
        except FileNotFoundError:
            logger.error("People data file not found: %s", PEOPLE_DATA_FILE)
            _people = []
        except Exception as e:
            logger.error("Error loading people data: %s", str(e))
            _people = []


def get_person(logon_id: Optional[str] = None,
               employee_id: Optional[str] = None) -> Optional[Person]:
    """Get a single person by LogonId or EmployeeId."""
    _ensure_loaded()

    if logon_id:
        for p in _people:
            if p.logon_id == logon_id:
                return p

    if employee_id:
        for p in _people:
            if p.employee_id == employee_id:
                return p

    return None


def get_matching_people(search_text: str, take: int = 10) -> List[Person]:
    """Search people by name or logon_id containing search_text."""
    _ensure_loaded()

    if not search_text or len(search_text) < 3:
        return []

    search_lower = search_text.lower()
    results = []
    for p in _people:
        if (search_lower in p.full_name.lower() or
                search_lower in p.logon_id.lower()):
            results.append(p)
            if len(results) >= take:
                break

    return results


def validate_person(logon_id: Optional[str] = None,
                    employee_id: Optional[str] = None) -> bool:
    """Validate that a person exists."""
    return get_person(logon_id=logon_id, employee_id=employee_id) is not None


def get_all_people() -> List[Person]:
    """Return all loaded people."""
    _ensure_loaded()
    return _people or []
