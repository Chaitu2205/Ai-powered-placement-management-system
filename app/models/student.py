from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import PlacementStatus


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    # NOTE: students <-> resumes is a circular FK relationship (a student has
    # many resumes, and points back at one "current" resume). use_alter=True
    # tells SQLAlchemy/Alembic to create this constraint in a separate ALTER
    # TABLE statement after both tables exist, avoiding a table-creation
    # ordering deadlock.
    current_resume_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "resumes.id", ondelete="SET NULL", use_alter=True, name="fk_students_current_resume"
        ),
        nullable=True,
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    batch_year: Mapped[Optional[int]] = mapped_column(nullable=True)
    cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    placement_status: Mapped[PlacementStatus] = mapped_column(
        Enum(PlacementStatus, native_enum=False, length=20),
        default=PlacementStatus.NOT_PLACED,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="student_profile")
    department: Mapped[Optional["Department"]] = relationship(back_populates="students")

    # All resume versions uploaded by this student (current_resume_id points to one of these).
    # foreign_keys is explicit on both sides of this relationship because there
    # are two distinct FK paths between students <-> resumes (resumes.student_id,
    # and students.current_resume_id) - without it SQLAlchemy cannot determine
    # which FK to join on and raises AmbiguousForeignKeysError.
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="student",
        foreign_keys="Resume.student_id",
        cascade="all, delete-orphan",
    )
    # Convenience read-only accessor for the student's currently-active resume.
    # viewonly=True because the "true" ownership/cascade relationship is
    # `resumes` above; this just follows current_resume_id for reads.
    current_resume: Mapped[Optional["Resume"]] = relationship(
        foreign_keys=[current_resume_id], viewonly=True
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    student_skills: Mapped[list["StudentSkill"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    interview_sessions: Mapped[list["InterviewSession"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} name={self.full_name}>"
