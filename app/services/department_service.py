from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate
from app.utils.exceptions import ConflictError, NotFoundError


def list_departments(db: Session) -> list[Department]:
    return list(db.execute(select(Department).order_by(Department.name)).scalars().all())


def get_department(db: Session, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise NotFoundError("Department not found")
    return department


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    exists = db.execute(
        select(Department).where(
            (Department.name == payload.name) | (Department.code == payload.code)
        )
    ).scalar_one_or_none()
    if exists is not None:
        raise ConflictError("A department with this name or code already exists")

    department = Department(name=payload.name, code=payload.code)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department
