from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.enums import JobStatus, JobType, UserRole
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate
from app.services.recruiter_service import get_recruiter_by_user_id
from app.services.skill_service import get_or_create_skill
from app.utils.exceptions import NotFoundError, PermissionDeniedError


def _assert_can_manage_job(db: Session, current_user: User, company: Company) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.RECRUITER:
        recruiter = get_recruiter_by_user_id(db, current_user.id)
        if company.recruiter_id == recruiter.id:
            return
    raise PermissionDeniedError("You do not have permission to manage jobs for this company")


def create_job(db: Session, current_user: User, payload: JobCreate) -> Job:
    company = db.get(Company, payload.company_id)
    if company is None:
        raise NotFoundError("Company not found")
    _assert_can_manage_job(db, current_user, company)

    job = Job(
        company_id=payload.company_id,
        placement_drive_id=payload.placement_drive_id,
        created_by=current_user.id,
        title=payload.title,
        description=payload.description,
        job_type=payload.job_type,
        location=payload.location,
        package_lpa=payload.package_lpa,
    )
    db.add(job)
    db.flush()  # assign job.id for the JobSkill rows below

    for required in payload.required_skills:
        skill = get_or_create_skill(db, required.skill_name)
        db.add(JobSkill(job_id=job.id, skill_id=skill.id, is_mandatory=required.is_mandatory))

    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> Job:
    job = db.execute(
        select(Job).where(Job.id == job_id).options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
    ).scalar_one_or_none()
    if job is None:
        raise NotFoundError("Job not found")
    return job


def list_jobs(
    db: Session,
    *,
    offset: int,
    limit: int,
    status_filter: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
    company_id: Optional[int] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[list[Job], int]:
    stmt = select(Job)
    count_stmt = select(func.count()).select_from(Job)

    if status_filter is not None:
        stmt = stmt.where(Job.status == status_filter)
        count_stmt = count_stmt.where(Job.status == status_filter)
    if job_type is not None:
        stmt = stmt.where(Job.job_type == job_type)
        count_stmt = count_stmt.where(Job.job_type == job_type)
    if company_id is not None:
        stmt = stmt.where(Job.company_id == company_id)
        count_stmt = count_stmt.where(Job.company_id == company_id)
    if location:
        pattern = f"%{location}%"
        stmt = stmt.where(Job.location.ilike(pattern))
        count_stmt = count_stmt.where(Job.location.ilike(pattern))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Job.title.ilike(pattern))
        count_stmt = count_stmt.where(Job.title.ilike(pattern))

    total = db.scalar(count_stmt) or 0
    rows = (
        db.execute(stmt.order_by(Job.created_at.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def update_job(db: Session, current_user: User, job: Job, payload: JobUpdate) -> Job:
    _assert_can_manage_job(db, current_user, job.company)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


def close_job(db: Session, current_user: User, job: Job) -> Job:
    _assert_can_manage_job(db, current_user, job.company)
    job.status = JobStatus.CLOSED
    db.commit()
    db.refresh(job)
    return job
