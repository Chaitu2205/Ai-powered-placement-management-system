from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recruiter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    recruiter: Mapped[Optional["Recruiter"]] = relationship(back_populates="companies")
    jobs: Mapped[list["Job"]] = relationship(back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name}>"
