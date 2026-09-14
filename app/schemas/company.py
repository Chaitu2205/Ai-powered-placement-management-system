from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    industry: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(default=None, max_length=255)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)


class CompanyRead(ORMBase):
    id: int
    recruiter_id: Optional[int]
    name: str
    industry: Optional[str]
    website: Optional[str]
    description: Optional[str]
    logo_url: Optional[str]
