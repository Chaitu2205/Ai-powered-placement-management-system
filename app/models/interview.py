from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import (
    DifficultyLevel,
    ExperienceLevel,
    InterviewType,
    SessionStatus,
)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )

    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=False, length=20), nullable=False
    )
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, native_enum=False, length=10), nullable=False
    )
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, native_enum=False, length=15), nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, native_enum=False, length=15),
        default=SessionStatus.IN_PROGRESS,
        nullable=False,
    )
    overall_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    student: Mapped["Student"] = relationship(back_populates="interview_sessions")
    job: Mapped[Optional["Job"]] = relationship(back_populates="interview_sessions")
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.order_index"
    )

    def __repr__(self) -> str:
        return f"<InterviewSession id={self.id} student_id={self.student_id} type={self.interview_type}>"


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=False, length=20), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    session: Mapped["InterviewSession"] = relationship(back_populates="questions")
    answer: Mapped[Optional["InterviewAnswer"]] = relationship(
        back_populates="question", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InterviewQuestion id={self.id} session_id={self.session_id}>"


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)

    relevance_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    correctness_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    completeness_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    communication_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)

    good_points_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    improvements_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    suggested_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Phase 10: a short, human-readable summary distinct from the structured
    # score/points fields above - what the frontend shows as "feedback" at a
    # glance, without the student having to read every sub-score.
    feedback_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    question: Mapped["InterviewQuestion"] = relationship(back_populates="answer")

    def __repr__(self) -> str:
        return f"<InterviewAnswer id={self.id} question_id={self.question_id} score={self.score}>"
