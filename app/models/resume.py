from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ResumeFileType


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[ResumeFileType] = mapped_column(
        Enum(ResumeFileType, native_enum=False, length=10), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Phase 6: raw text extracted from the uploaded PDF/DOCX at upload time.
    # Nullable because extraction can legitimately yield nothing (e.g. a
    # scanned/image-only PDF) - that's a valid state, not an error.
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    student: Mapped["Student"] = relationship(
        back_populates="resumes", foreign_keys=[student_id]
    )
    analyses: Mapped[list["ResumeAnalysis"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeAnalysis.analyzed_at.desc()"
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume id={self.id} student_id={self.student_id} file={self.original_filename}>"
