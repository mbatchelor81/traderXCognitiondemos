"""
TradeAudit SQLAlchemy model.
Persists audit trail records for trade state changes and lifecycle events.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database import Base
from app.config import DEFAULT_TENANT


class TradeAudit(Base):
    __tablename__ = "trade_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, default=DEFAULT_TENANT)
    account_id = Column(Integer, nullable=False)
    old_state = Column(String(20), nullable=True)
    new_state = Column(String(20), nullable=False)
    action = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
