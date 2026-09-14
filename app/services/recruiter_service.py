from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recruiter import Recruiter
from app.schemas.recruiter import RecruiterUpdate
from app.utils.exceptions import NotFoundError


def get_recruiter_by_user_id(db: Session, user_id: int) -> Recruiter:
    recruiter = db.execute(
        select(Recruiter).where(Recruiter.user_id == user_id)
    ).scalar_one_or_none()
    if recruiter is None:
        raise NotFoundError("Recruiter profile not found")
    return recruiter


def get_recruiter(db: Session, recruiter_id: int) -> Recruiter:
    recruiter = db.get(Recruiter, recruiter_id)
    if recruiter is None:
        raise NotFoundError("Recruiter not found")
    return recruiter


def list_recruiters(db: Session) -> list[Recruiter]:
    return list(db.execute(select(Recruiter).order_by(Recruiter.full_name)).scalars().all())


def update_recruiter(db: Session, recruiter: Recruiter, payload: RecruiterUpdate) -> Recruiter:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recruiter, field, value)
    db.commit()
    db.refresh(recruiter)
    return recruiter
