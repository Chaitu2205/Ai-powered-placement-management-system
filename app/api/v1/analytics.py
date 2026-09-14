from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.analytics import AdminAnalytics, RecruiterAnalytics, StudentAnalytics
from app.security.dependencies import require_role
from app.services import analytics_service
from app.services.recruiter_service import get_recruiter_by_user_id
from app.services.student_service import get_student_by_user_id

router = APIRouter()


@router.get("/student", response_model=StudentAnalytics)
def get_student_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> StudentAnalytics:
    """A student's own analytics only - there is no cross-student view of this endpoint."""
    student = get_student_by_user_id(db, current_user.id)
    return analytics_service.get_student_analytics(db, student)


@router.get("/recruiter", response_model=RecruiterAnalytics)
def get_recruiter_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> RecruiterAnalytics:
    """A recruiter's own company/jobs analytics only - scoped inside the service, not just by role."""
    recruiter = get_recruiter_by_user_id(db, current_user.id)
    return analytics_service.get_recruiter_analytics(db, recruiter)


@router.get("/admin", response_model=AdminAnalytics)
def get_admin_analytics(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> AdminAnalytics:
    """System-wide analytics - admin only."""
    return analytics_service.get_admin_analytics(db)
