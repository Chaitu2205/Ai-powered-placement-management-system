from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ResumeAnalysis(Base):
    """
    One row per AI analysis run on a resume. A resume can be re-analyzed
    (e.g. after the student updates it), so this is versioned rather than
    overwritten - `analyzed_at` orders the history.
    """
    __tablename__ = "resume_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    extracted_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    extracted_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    education_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    projects_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    internships_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    certifications_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    experience_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detected_skills_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    strengths_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    weaknesses_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_skills_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    suggestions_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ats_keywords_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    resume: Mapped["Resume"] = relationship(back_populates="analyses")

    def __repr__(self) -> str:
        return f"<ResumeAnalysis id={self.id} resume_id={self.resume_id} score={self.overall_score}>"
