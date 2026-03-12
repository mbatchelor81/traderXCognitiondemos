"""Trade and Position SQLAlchemy models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from app.config import TENANT_ID


class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, default=TENANT_ID)
    account_id = Column(Integer, nullable=False)
    security = Column(String(50), nullable=False)
    side = Column(String(4), nullable=False)
    quantity = Column(Integer, nullable=False)
    state = Column(String(20), nullable=False, default="New")
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
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
