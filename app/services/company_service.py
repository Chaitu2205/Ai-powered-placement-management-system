from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.services.recruiter_service import get_recruiter_by_user_id
from app.utils.exceptions import NotFoundError, PermissionDeniedError


def list_companies(db: Session, *, offset: int, limit: int, search: Optional[str] = None) -> tuple[list[Company], int]:
    stmt = select(Company)
    count_stmt = select(func.count()).select_from(Company)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Company.name.ilike(pattern))
        count_stmt = count_stmt.where(Company.name.ilike(pattern))

    total = db.scalar(count_stmt) or 0
    rows = db.execute(stmt.order_by(Company.name).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_company(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    return company


def create_company(db: Session, current_user: User, payload: CompanyCreate) -> Company:
    recruiter_id = None
    if current_user.role == UserRole.RECRUITER:
        recruiter_id = get_recruiter_by_user_id(db, current_user.id).id

    company = Company(recruiter_id=recruiter_id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def _assert_can_manage(db: Session, current_user: User, company: Company) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.RECRUITER:
        recruiter = get_recruiter_by_user_id(db, current_user.id)
        if company.recruiter_id == recruiter.id:
            return
    raise PermissionDeniedError("You do not have permission to manage this company")


def update_company(db: Session, current_user: User, company: Company, payload: CompanyUpdate) -> Company:
    _assert_can_manage(db, current_user, company)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
