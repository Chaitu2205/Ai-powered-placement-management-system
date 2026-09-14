from typing import Optional

from fastapi import status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.company import Company
from app.models.enums import ApplicationStatus, AuditAction, JobStatus, PlacementStatus, UserRole
from app.models.job import Job
from app.models.notification import Notification
from app.models.student import Student
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate
from app.services import audit_service
from app.services.recruiter_service import get_recruiter_by_user_id
from app.services.student_service import get_student_by_user_id
from app.utils.exceptions import AppException, ConflictError, NotFoundError, PermissionDeniedError


def apply_to_job(db: Session, current_user: User, payload: ApplicationCreate) -> Application:
    student = get_student_by_user_id(db, current_user.id)

    job = db.get(Job, payload.job_id)
    if job is None:
        raise NotFoundError("Job not found")
    if job.status != JobStatus.OPEN:
        raise AppException("This job is no longer accepting applications", status_code=http_status.HTTP_400_BAD_REQUEST)

    existing = db.execute(
        select(Application).where(
            Application.student_id == student.id, Application.job_id == job.id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("You have already applied to this job")

    resume_id = payload.resume_id or student.current_resume_id

    application = Application(
        student_id=student.id,
        job_id=job.id,
        resume_id=resume_id,
        status=ApplicationStatus.APPLIED,
    )
    db.add(application)

    audit_service.log_action(
        db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        entity_type="application",
        details={"job_id": job.id, "student_id": student.id},
    )

    db.commit()
    db.refresh(application)
    return application


def get_application(db: Session, application_id: int) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise NotFoundError("Application not found")
    return application


def _assert_can_view_or_manage(db: Session, current_user: User, application: Application) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.STUDENT:
        student = get_student_by_user_id(db, current_user.id)
        if application.student_id == student.id:
            return
    if current_user.role == UserRole.RECRUITER:
        recruiter = get_recruiter_by_user_id(db, current_user.id)
        if application.job.company.recruiter_id == recruiter.id:
            return
    raise PermissionDeniedError("You do not have permission to view this application")


def list_my_applications(db: Session, current_user: User) -> list[Application]:
    student = get_student_by_user_id(db, current_user.id)
    return list(
        db.execute(
            select(Application)
            .where(Application.student_id == student.id)
            .order_by(Application.created_at.desc())
        )
        .scalars()
        .all()
    )


def list_applications(
    db: Session,
    current_user: User,
    *,
    offset: int,
    limit: int,
    job_id: Optional[int] = None,
    status_filter: Optional[ApplicationStatus] = None,
) -> tuple[list[Application], int]:
    """Admin: sees everything. Recruiter: only applications for jobs at their own company."""
    stmt = select(Application)
    count_stmt = select(func.count()).select_from(Application)

    if current_user.role == UserRole.RECRUITER:
        recruiter = get_recruiter_by_user_id(db, current_user.id)
        stmt = (
            stmt.join(Job, Application.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .where(Company.recruiter_id == recruiter.id)
        )
        count_stmt = (
            count_stmt.join(Job, Application.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .where(Company.recruiter_id == recruiter.id)
        )

    if job_id is not None:
        stmt = stmt.where(Application.job_id == job_id)
        count_stmt = count_stmt.where(Application.job_id == job_id)
    if status_filter is not None:
        stmt = stmt.where(Application.status == status_filter)
        count_stmt = count_stmt.where(Application.status == status_filter)

    total = db.scalar(count_stmt) or 0
    rows = (
        db.execute(stmt.order_by(Application.created_at.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def update_application_status(
    db: Session, current_user: User, application: Application, payload: ApplicationStatusUpdate
) -> Application:
    if current_user.role not in (UserRole.ADMIN, UserRole.RECRUITER):
        raise PermissionDeniedError("Only admins and recruiters can update application status")
    if current_user.role == UserRole.RECRUITER:
        recruiter = get_recruiter_by_user_id(db, current_user.id)
        if application.job.company.recruiter_id != recruiter.id:
            raise PermissionDeniedError("You do not manage the job this application is for")

    old_status = application.status
    application.status = payload.status

    audit_service.log_action(
        db,
        user_id=current_user.id,
        action=AuditAction.STATUS_CHANGE,
        entity_type="application",
        entity_id=application.id,
        details={"from": old_status.value, "to": payload.status.value},
    )

    student = db.get(Student, application.student_id)

    # Phase 11 note: Student.placement_status existed since Phase 1/2 but
    # nothing ever set it away from the NOT_PLACED default - meaning the
    # admin "placement percentage" analytics metric would always read 0%.
    # Wiring it here (minimal, additive) is what makes that metric mean
    # anything. SHORTLISTED never downgrades an already-SELECTED student.
    if payload.status == ApplicationStatus.SELECTED:
        student.placement_status = PlacementStatus.SELECTED
    elif payload.status == ApplicationStatus.SHORTLISTED and student.placement_status != PlacementStatus.SELECTED:
        student.placement_status = PlacementStatus.SHORTLISTED

    notification = Notification(
        user_id=student.user_id,
        title="Application status updated",
        message=f"Your application status changed to {payload.status.value}.",
    )
    db.add(notification)

    db.commit()
    db.refresh(application)
    return application
