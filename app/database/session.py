"""
Database engine + session management.

Provides:
- `engine`: the SQLAlchemy engine, built from DATABASE_URL
- `SessionLocal`: a session factory
- `get_db`: a FastAPI dependency that yields a session and guarantees it is
  closed after the request, even if an exception is raised.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

settings = get_settings()

# pool_pre_ping avoids "MySQL server has gone away" errors on idle connections.
# pool_recycle prevents connections from being dropped by MySQL's wait_timeout.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
