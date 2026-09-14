from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import JobStatus, JobType
from app.schemas.common import ORMBase
from app.schemas.skill import SkillRead


class JobSkillInput(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    is_mandatory: bool = True


class JobBase(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10)
    job_type: JobType = JobType.FULL_TIME
    location: Optional[str] = Field(default=None, max_length=150)
    package_lpa: Optional[Decimal] = Field(default=None, ge=0)
    placement_drive_id: Optional[int] = None


class JobCreate(JobBase):
    company_id: int
    required_skills: list[JobSkillInput] = Field(default_factory=list)


class JobUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=10)
    job_type: Optional[JobType] = None
    location: Optional[str] = Field(default=None, max_length=150)
    package_lpa: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[JobStatus] = None


class JobRead(ORMBase):
    id: int
    company_id: int
    placement_drive_id: Optional[int]
    title: str
    description: str
    job_type: JobType
    location: Optional[str]
    package_lpa: Optional[Decimal]
    status: JobStatus


class JobSkillRead(ORMBase):
    is_mandatory: bool
    skill: SkillRead


class JobDetailRead(JobRead):
    """JobRead plus the resolved list of required skills - used by GET /jobs/{id}."""
    job_skills: list[JobSkillRead] = Field(default_factory=list)
