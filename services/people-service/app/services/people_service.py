"""People data service — loads people from JSON."""

import json
import logging
import os
from typing import Dict, List, Optional

from app.config import DATA_DIR
from app.models.person import Person

logger = logging.getLogger(__name__)

_people: List[Person] = []
_people_by_logon: Dict[str, Person] = {}


def load_people():
    """Load people from JSON file into memory."""
    global _people, _people_by_logon
    json_path = os.path.join(DATA_DIR, "people.json")
    if not os.path.exists(json_path):
        logger.warning("People JSON not found at %s", json_path)
        return

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    _people = []
    _people_by_logon = {}
    for entry in raw:
        full_name = entry.get("FullName", entry.get("full_name", ""))
        name_parts = full_name.split(" ", 1)
        first_name = entry.get("FirstName", entry.get("first_name", name_parts[0] if name_parts else ""))
        last_name = entry.get("LastName", entry.get("last_name", name_parts[1] if len(name_parts) > 1 else ""))
        avatar_url = entry.get("AvatarUrl", entry.get("avatar_url", entry.get("PhotoUrl", entry.get("photo_url", ""))))
        person = Person(
            logon_id=entry.get("LogonId", entry.get("logon_id", "")),
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            email=entry.get("Email", entry.get("email", "")),
            department=entry.get("Department", entry.get("department", "")),
            avatar_url=avatar_url,
        )
        _people.append(person)
        _people_by_logon[person.logon_id.lower()] = person

    logger.info("Loaded %d people from JSON", len(_people))


def get_person(logon_id: str) -> Optional[Person]:
    return _people_by_logon.get(logon_id.lower())


def get_matching_people(query: str) -> List[Person]:
    query_lower = query.lower()
    return [
        p for p in _people
        if query_lower in p.full_name.lower()
        or query_lower in p.logon_id.lower()
        or query_lower in p.email.lower()
    ]


def validate_person(logon_id: str) -> bool:
    return logon_id.lower() in _people_by_logon
