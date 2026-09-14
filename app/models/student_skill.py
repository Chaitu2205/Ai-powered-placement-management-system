from typing import Optional

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ProficiencyLevel, SkillSource


class StudentSkill(Base):
    """
    Many-to-many association between students and skills, enriched with
    proficiency and where the skill came from (manually added vs. AI-extracted
    from a resume).
    """
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proficiency: Mapped[Optional[ProficiencyLevel]] = mapped_column(
        Enum(ProficiencyLevel, native_enum=False, length=20), nullable=True
    )
    source: Mapped[SkillSource] = mapped_column(
        Enum(SkillSource, native_enum=False, length=20),
        default=SkillSource.MANUAL,
        nullable=False,
    )

    student: Mapped["Student"] = relationship(back_populates="student_skills")
    skill: Mapped["Skill"] = relationship(back_populates="student_links")

    def __repr__(self) -> str:
        return f"<StudentSkill student_id={self.student_id} skill_id={self.skill_id}>"
