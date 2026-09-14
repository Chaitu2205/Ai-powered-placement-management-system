"""
Importing this package guarantees every ORM model is registered on
`Base.metadata`. This is required by Alembic's `--autogenerate` (see
alembic/env.py) and is also a convenient single import for the rest of the
app: `from app import models` then `models.User`, `models.Job`, etc.
"""
from app.database.base import Base  # noqa: F401

from app.models.user import User  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.recruiter import Recruiter  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.placement_drive import PlacementDrive  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.student_skill import StudentSkill  # noqa: F401
from app.models.job_skill import JobSkill  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.interview import (  # noqa: F401
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
)
from app.models.notification import Notification  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Department",
    "Student",
    "Recruiter",
    "Company",
    "PlacementDrive",
    "Job",
    "Skill",
    "StudentSkill",
    "JobSkill",
    "Resume",
    "ResumeAnalysis",
    "Application",
    "InterviewSession",
    "InterviewQuestion",
    "InterviewAnswer",
    "Notification",
    "AuditLog",
]
