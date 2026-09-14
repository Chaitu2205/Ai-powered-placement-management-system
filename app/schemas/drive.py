from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import DriveStatus
from app.schemas.common import ORMBase


class DriveBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    eligible_departments: Optional[str] = Field(default=None, max_length=255)
    min_cgpa: Optional[Decimal] = Field(default=None, ge=0, le=10)


class DriveCreate(DriveBase):
    pass


class DriveUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    eligible_departments: Optional[str] = Field(default=None, max_length=255)
    min_cgpa: Optional[Decimal] = Field(default=None, ge=0, le=10)
    status: Optional[DriveStatus] = None


class DriveRead(ORMBase):
    id: int
    name: str
    start_date: Optional[date]
    end_date: Optional[date]
    eligible_departments: Optional[str]
    min_cgpa: Optional[Decimal]
    status: DriveStatus
