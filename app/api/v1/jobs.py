from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import JobStatus, JobType, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.job import JobCreate, JobDetailRead, JobRead, JobUpdate
from app.schemas.job_match import JobMatchRead, RecommendedJobRead
from app.security.dependencies import get_current_user, require_role
from app.services import job_matching_service, job_service
from app.services.student_service import get_student_by_user_id
from app.utils.pagination import PageParams, pagination_params

router = APIRouter()


@router.get("", response_model=PaginatedResponse[JobRead])
def list_jobs(
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
    job_type: Optional[JobType] = Query(default=None),
    company_id: Optional[int] = Query(default=None),
    location: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Search by job title"),
    page_params: PageParams = Depends(pagination_params),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> PaginatedResponse:
    jobs, total = job_service.list_jobs(
        db,
        offset=page_params.offset,
        limit=page_params.page_size,
        status_filter=status_filter,
        job_type=job_type,
        company_id=company_id,
        location=location,
        search=search,
    )
    return PaginatedResponse[JobRead](
        items=jobs, total=total, page=page_params.page, page_size=page_params.page_size
    )


@router.post("", response_model=JobDetailRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> JobDetailRead:
    job = job_service.create_job(db, current_user, payload)
    return job_service.get_job(db, job.id)


@router.get("/recommended", response_model=list[RecommendedJobRead])
def get_recommended_jobs(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> list:
    """
    Ranks currently-open jobs for the authenticated student by a
    deterministic skill-match score (see job_matching_service). Registered
    BEFORE /{job_id} - otherwise Starlette would try to parse "recommended"
    as a job_id and 422 instead of matching this route.
    """
    student = get_student_by_user_id(db, current_user.id)
    return job_matching_service.get_recommended_jobs(db, student, limit=limit)


@router.get("/{job_id}", response_model=JobDetailRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> JobDetailRead:
    return job_service.get_job(db, job_id)


@router.get("/{job_id}/match", response_model=JobMatchRead)
def get_job_match(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> JobMatchRead:
    """Match score for the authenticated student against one specific job."""
    student = get_student_by_user_id(db, current_user.id)
    job = job_service.get_job(db, job_id)
    return job_matching_service.compute_match(db, student, job)


@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> JobRead:
    job = job_service.get_job(db, job_id)
    return job_service.update_job(db, current_user, job, payload)


@router.post("/{job_id}/close", response_model=JobRead)
def close_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> JobRead:
    job = job_service.get_job(db, job_id)
    return job_service.close_job(db, current_user, job)
