"""
Position SQLAlchemy model — the only table owned by position-service.

Ported from traderx-monolith/app/models/position.py. The ForeignKey to
accounts.id is dropped: accounts live in another service's database and
position-service never joins across service boundaries.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.config import TENANT_ID
from app.database import Base


class Position(Base):
    __tablename__ = "positions"

    account_id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), primary_key=True, default=TENANT_ID)
    security = Column(String(50), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "accountId": self.account_id,
            "tenant_id": self.tenant_id,
            "security": self.security,
            "quantity": self.quantity,
            "updated": self.updated.isoformat() if self.updated else None,
        }
