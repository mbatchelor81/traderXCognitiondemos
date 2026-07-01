"""
TradeAudit SQLAlchemy model.
Persists every trade state change for audit trail purposes.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from app.database import Base
from app.config import *  # noqa: F401,F403 — intentional global config import


class TradeAudit(Base):
    __tablename__ = "trade_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    tenant_id = Column(String(50), nullable=False)
    account_id = Column(Integer, nullable=False)
    old_state = Column(String(20), nullable=True)
    new_state = Column(String(20), nullable=False)
    event_type = Column(String(30), nullable=False)
    details = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_trade_audit_trade_id", "trade_id"),
        Index("ix_trade_audit_tenant_id", "tenant_id"),
    )

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
