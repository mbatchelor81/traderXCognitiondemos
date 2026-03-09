"""Person model — plain data model loaded from JSON."""

from pydantic import BaseModel


class Person(BaseModel):
    logon_id: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    department: str
    avatar_url: str = ""

    def to_dict(self):
        return {
            "LogonId": self.logon_id,
            "FirstName": self.first_name,
            "LastName": self.last_name,
            "FullName": self.full_name,
            "Email": self.email,
            "Department": self.department,
            "AvatarUrl": self.avatar_url,
        }
