"""Person model (plain data model loaded from JSON)."""


class Person:
    """Represents a person in the directory service."""

    def __init__(self, logon_id: str, full_name: str, email: str,
                 employee_id: str, department: str, photo_url: str = ""):
        self.logon_id = logon_id
        self.full_name = full_name
        self.email = email
        self.employee_id = employee_id
        self.department = department
        self.photo_url = photo_url

    def to_dict(self):
        return {
            "LogonId": self.logon_id,
            "FullName": self.full_name,
            "Email": self.email,
            "EmployeeId": self.employee_id,
            "Department": self.department,
            "PhotoUrl": self.photo_url,
        }

    @staticmethod
    def from_dict(data: dict) -> "Person":
        return Person(
            logon_id=data.get("LogonId", ""),
            full_name=data.get("FullName", ""),
            email=data.get("Email", ""),
            employee_id=data.get("EmployeeId", ""),
            department=data.get("Department", ""),
            photo_url=data.get("PhotoUrl", ""),
        )
