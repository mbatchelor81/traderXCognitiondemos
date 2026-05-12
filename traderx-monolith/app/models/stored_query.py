"""
StoredQuery SQLAlchemy model.
Represents a versioned, parameterized query definition for billing data extraction.
"""

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import Base


class StoredQuery(Base):
    __tablename__ = "stored_queries"
    __table_args__ = (
        UniqueConstraint("qualified_name", "version", "tenant_id",
                         name="uq_query_name_version_tenant"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    qualified_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    query_type = Column(String(100), nullable=False)
    query_definition = Column(Text, nullable=False)
    parameters_schema = Column(Text, nullable=True)
    tenant_id = Column(String(50), nullable=False, default=DEFAULT_TENANT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "qualifiedName": self.qualified_name,
            "version": self.version,
            "description": self.description,
            "queryType": self.query_type,
            "queryDefinition": json.loads(self.query_definition),
            "parametersSchema": (
                json.loads(self.parameters_schema)
                if self.parameters_schema else None
            ),
            "tenant_id": self.tenant_id,
            "createdAt": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
