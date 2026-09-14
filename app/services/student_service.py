from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PlacementStatus
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentUpdate
from app.utils.exceptions import NotFoundError


def get_student_by_user_id(db: Session, user_id: int) -> Student:
    student = db.execute(select(Student).where(Student.user_id == user_id)).scalar_one_or_none()
    if student is None:
        raise NotFoundError("Student profile not found")
    return student


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFoundError("Student not found")
    return student


def update_student(db: Session, student: Student, payload: StudentUpdate) -> Student:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def list_students(
    db: Session,
    *,
    offset: int,
    limit: int,
    department_id: Optional[int] = None,
    placement_status: Optional[PlacementStatus] = None,
    search: Optional[str] = None,
) -> tuple[list[Student], int]:
    stmt = select(Student)
    count_stmt = select(func.count()).select_from(Student)

    if department_id is not None:
        stmt = stmt.where(Student.department_id == department_id)
        count_stmt = count_stmt.where(Student.department_id == department_id)
    if placement_status is not None:
        stmt = stmt.where(Student.placement_status == placement_status)
        count_stmt = count_stmt.where(Student.placement_status == placement_status)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Student.full_name.ilike(pattern))
        count_stmt = count_stmt.where(Student.full_name.ilike(pattern))

    total = db.scalar(count_stmt) or 0
    rows = db.execute(stmt.order_by(Student.full_name).offset(offset).limit(limit)).scalars().all()
    return list(rows), total
