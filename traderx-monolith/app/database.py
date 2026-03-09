"""
Database module for TraderX.
Provides SQLAlchemy engine, session factory, and declarative base.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL, DATABASE_ECHO

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
    """Create all database tables if they don't exist."""
    from app.models.account import Account, AccountUser  # noqa: F811
    from app.models.trade import Trade  # noqa: F811
    from app.models.position import Position  # noqa: F811

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables — use with caution."""
    Base.metadata.drop_all(bind=engine)
