"""
Database wiring for the trading-service.
This service owns exactly one table: `trades`.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_ECHO, DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=DATABASE_ECHO,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create this service's tables if they don't exist."""
    from app.models.trade import Trade  # noqa: F401 — registers the mapping

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop this service's tables — use with caution."""
    Base.metadata.drop_all(bind=engine)
