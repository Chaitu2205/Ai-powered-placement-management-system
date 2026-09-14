from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import DriveStatus


class PlacementDrive(Base, TimestampMixin):
    __tablename__ = "placement_drives"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    eligible_departments: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Comma-separated department codes"
    )
    min_cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    status: Mapped[DriveStatus] = mapped_column(
        Enum(DriveStatus, native_enum=False, length=20),
        default=DriveStatus.UPCOMING,
        nullable=False,
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="placement_drive")

    def __repr__(self) -> str:
        return f"<PlacementDrive id={self.id} name={self.name}>"
