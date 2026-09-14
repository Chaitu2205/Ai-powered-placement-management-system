from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import PlacementStatus
from app.schemas.common import ORMBase


class StudentBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)
    department_id: Optional[int] = None
    batch_year: Optional[int] = Field(default=None, ge=1990, le=2100)
    cgpa: Optional[Decimal] = Field(default=None, ge=0, le=10)
    date_of_birth: Optional[date] = None


class StudentUpdate(StudentBase):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)


class StudentRead(ORMBase):
    id: int
    user_id: int
    full_name: str
    phone: Optional[str]
    department_id: Optional[int]
    batch_year: Optional[int]
    cgpa: Optional[Decimal]
    placement_status: PlacementStatus
    current_resume_id: Optional[int]


class StudentListItem(ORMBase):
    """Slim version used in admin/recruiter list views."""
    id: int
    full_name: str
    department_id: Optional[int]
    batch_year: Optional[int]
    cgpa: Optional[Decimal]
    placement_status: PlacementStatus
