"""Account and AccountUser SQLAlchemy models — owned by account-service."""

from sqlalchemy import Column, ForeignKey, Integer, String

from app.config import TENANT_ID
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, default=TENANT_ID)
    display_name = Column(String(50), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "displayName": self.display_name,
        }


class AccountUser(Base):
    __tablename__ = "account_users"

    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    tenant_id = Column(String(50), primary_key=True, default=TENANT_ID)
    username = Column(String(100), primary_key=True)

    def to_dict(self) -> dict:
        return {
            "accountId": self.account_id,
            "tenant_id": self.tenant_id,
            "username": self.username,
        }
