"""
Trade SQLAlchemy model — the only table owned by the trading-service.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.config import TENANT_ID
from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, default=TENANT_ID, index=True)
    # Accounts live in account-service; this is a logical reference, not a FK.
    account_id = Column(Integer, nullable=False, index=True)
    security = Column(String(50), nullable=False)
    side = Column(String(4), nullable=False)  # Buy or Sell
    quantity = Column(Integer, nullable=False)
    state = Column(String(20), nullable=False, default="New")
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "accountId": self.account_id,
            "security": self.security,
            "side": self.side,
            "quantity": self.quantity,
            "state": self.state,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }
