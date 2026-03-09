"""
Position SQLAlchemy model.
Single-tenant: no tenant_id column.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base


class Position(Base):
    __tablename__ = "positions"

    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    security = Column(String(50), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "accountId": self.account_id,
            "security": self.security,
            "quantity": self.quantity,
            "updated": self.updated.isoformat() if self.updated else None,
        }
