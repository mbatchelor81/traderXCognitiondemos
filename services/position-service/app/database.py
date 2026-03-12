"""Database module for Position Service."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import DATABASE_URL, DATABASE_ECHO

_extra_kwargs = {}
if "sqlite" in DATABASE_URL:
    _extra_kwargs["connect_args"] = {"check_same_thread": False}
    if ":memory:" in DATABASE_URL:
        _extra_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, echo=DATABASE_ECHO, **_extra_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app.models import Position  # noqa
    Base.metadata.create_all(bind=engine)
