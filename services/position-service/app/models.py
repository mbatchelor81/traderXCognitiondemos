"""Position SQLAlchemy model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from app.config import TENANT_ID


class Position(Base):
    __tablename__ = "positions"
    account_id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), primary_key=True, default=TENANT_ID)
    security = Column(String(50), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "accountId": self.account_id,
            "tenant_id": self.tenant_id,
            "security": self.security,
            "quantity": self.quantity,
            "updated": self.updated.isoformat() if self.updated else None,
        }
