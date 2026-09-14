from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.recruiter import RecruiterRead, RecruiterUpdate
from app.security.dependencies import require_role
from app.services import recruiter_service

router = APIRouter()


@router.get("/me", response_model=RecruiterRead)
def read_own_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> RecruiterRead:
    return recruiter_service.get_recruiter_by_user_id(db, current_user.id)


@router.put("/me", response_model=RecruiterRead)
def update_own_profile(
    payload: RecruiterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> RecruiterRead:
    recruiter = recruiter_service.get_recruiter_by_user_id(db, current_user.id)
    return recruiter_service.update_recruiter(db, recruiter, payload)


@router.get("", response_model=list[RecruiterRead])
def list_recruiters(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> list:
    return recruiter_service.list_recruiters(db)


@router.get("/{recruiter_id}", response_model=RecruiterRead)
def get_recruiter(
    recruiter_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> RecruiterRead:
    return recruiter_service.get_recruiter(db, recruiter_id)
