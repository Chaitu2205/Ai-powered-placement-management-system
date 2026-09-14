from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.enums import ApplicationStatus
from app.schemas.common import ORMBase


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: Optional[int] = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationRead(ORMBase):
    id: int
    student_id: int
    job_id: int
    resume_id: Optional[int]
    status: ApplicationStatus
    match_score: Optional[Decimal]
