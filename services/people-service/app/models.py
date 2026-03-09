"""Person model (non-DB, loaded from JSON)."""
from pydantic import BaseModel
from typing import Optional


class Person(BaseModel):
    LogonId: str
    FullName: str
    Email: str
    Department: str
    AvatarUrl: Optional[str] = None
