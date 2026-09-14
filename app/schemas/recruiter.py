from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class RecruiterBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    designation: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)


class RecruiterUpdate(RecruiterBase):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)


class RecruiterRead(ORMBase):
    id: int
    user_id: int
    full_name: str
    designation: Optional[str]
    phone: Optional[str]
