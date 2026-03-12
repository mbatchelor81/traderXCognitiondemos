"""People service - loads person data from JSON."""
import json
import logging
import os
from typing import Dict, List, Optional

from app.models import Person

logger = logging.getLogger(__name__)

_people: Dict[str, Person] = {}


def load_people_from_json() -> None:
    """Load people data from JSON file."""
    global _people
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "people.json")
    if not os.path.exists(json_path):
        logger.warning("People data JSON not found at %s", json_path)
        return
    with open(json_path, "r") as f:
        data = json.load(f)
    for entry in data:
        logon_id = entry.get("LogonId", "")
        if logon_id:
            _people[logon_id] = Person(**entry)
    logger.info("Loaded %d people from JSON", len(_people))


def get_person(logon_id: str) -> Optional[Person]:
    return _people.get(logon_id)


def get_matching_people(search: str) -> List[Person]:
    search_lower = search.lower()
    return [
        p for p in _people.values()
        if search_lower in p.FullName.lower()
        or search_lower in p.LogonId.lower()
        or search_lower in p.Email.lower()
    ]


def validate_person(logon_id: str) -> Dict:
    person = _people.get(logon_id)
    if person:
        return {"IsValid": True, "FullName": person.FullName}
    return {"IsValid": False, "FullName": None}
