from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import JobStatus, JobType


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    placement_drive_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("placement_drives.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, native_enum=False, length=20), default=JobType.FULL_TIME, nullable=False
    )
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    package_lpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=20), default=JobStatus.OPEN, nullable=False, index=True
    )

    company: Mapped["Company"] = relationship(back_populates="jobs")
    placement_drive: Mapped[Optional["PlacementDrive"]] = relationship(back_populates="jobs")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])

    job_skills: Mapped[list["JobSkill"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(back_populates="job")

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title}>"
