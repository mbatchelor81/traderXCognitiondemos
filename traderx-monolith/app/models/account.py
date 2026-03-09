"""
Account and AccountUser SQLAlchemy models.
Single-tenant: no tenant_id column. Isolation enforced at infrastructure level.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "displayName": self.display_name,
        }


class AccountUser(Base):
    __tablename__ = "account_users"

    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    username = Column(String(100), primary_key=True)

    def to_dict(self):
        return {
            "accountId": self.account_id,
            "username": self.username,
        }
