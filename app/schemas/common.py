from datetime import datetime
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str
    message: str


class ORMBase(BaseModel):
    """Base class for schemas that read data out of SQLAlchemy ORM objects."""
    model_config = {"from_attributes": True}


class TimestampedSchema(ORMBase):
    created_at: datetime
    updated_at: datetime


class ErrorResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic page wrapper used by every list endpoint (students, jobs, applications, ...)."""
    items: List[T]
    total: int
    page: int
    page_size: int
