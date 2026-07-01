"""
TradeAudit SQLAlchemy model.
Persists every trade state change for audit trail purposes.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from app.database import Base
from app.config import *  # noqa: F401,F403 — intentional global config import


class TradeAudit(Base):
    __tablename__ = "trade_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    account_id = Column(Integer, nullable=False)
    old_state = Column(String(20), nullable=True)
    new_state = Column(String(20), nullable=False)
    event_type = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tradeId": self.trade_id,
            "tenantId": self.tenant_id,
            "accountId": self.account_id,
            "oldState": self.old_state,
            "newState": self.new_state,
            "eventType": self.event_type,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
