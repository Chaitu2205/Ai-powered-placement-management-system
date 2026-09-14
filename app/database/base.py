"""
Declarative base for all SQLAlchemy models.

This module has no dependency on the rest of the app so it can be imported
safely from anywhere (models, alembic env.py, etc.) without circular imports.
"""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""
    pass


class TimestampMixin:
    """
    Mixin that adds created_at / updated_at columns, automatically managed
    by the database server.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
