"""
Analytics aggregation.

Every metric here is computed with SQL aggregation (COUNT/GROUP BY/AVG)
rather than loading full tables into Python and counting in application
code. The one exception is `recommended_jobs`, which reuses the existing
`job_matching_service.get_recommended_jobs` - that function already loads
open jobs with `selectinload` (no N+1) and is capped by `limit`, so reusing
it here (rather than duplicating matching logic) is the right trade-off.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.company import Company
from app.models.enums import ApplicationStatus, JobStatus, PlacementStatus
from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession
from app.models.job import Job
from app.models.recruiter import Recruiter
from app.models.resume_analysis import ResumeAnalysis
from app.models.student import Student
from app.models.user import User
from app.schemas.analytics import (
    AdminAnalytics,
    JobApplicantCount,
    MonthCount,
    RecruiterAnalytics,
    StatusCount,
    StudentAnalytics,
)
from app.services import job_matching_service

RECOMMENDED_JOBS_LIMIT = 5


def _status_counts(db: Session, status_column) -> list[StatusCount]:
    rows = db.execute(select(status_column, func.count()).group_by(status_column)).all()
    return [StatusCount(status=status.value if hasattr(status, "value") else str(status), count=count) for status, count in rows]


def get_student_analytics(db: Session, student: Student) -> StudentAnalytics:
    total_applications = db.scalar(
        select(func.count()).select_from(Application).where(Application.student_id == student.id)
    ) or 0

    status_rows = db.execute(
        select(Application.status, func.count())
        .where(Application.student_id == student.id)
        .group_by(Application.status)
    ).all()
    applications_by_status = [StatusCount(status=s.value, count=c) for s, c in status_rows]

    open_jobs_count = db.scalar(
        select(func.count()).select_from(Job).where(Job.status == JobStatus.OPEN)
    ) or 0

    recommended_jobs = job_matching_service.get_recommended_jobs(db, student, limit=RECOMMENDED_JOBS_LIMIT)

    total_interview_sessions = db.scalar(
        select(func.count()).select_from(InterviewSession).where(InterviewSession.student_id == student.id)
    ) or 0

    questions_answered = db.scalar(
        select(func.count())
        .select_from(InterviewAnswer)
        .join(InterviewQuestion, InterviewAnswer.question_id == InterviewQuestion.id)
        .join(InterviewSession, InterviewQuestion.session_id == InterviewSession.id)
        .where(InterviewSession.student_id == student.id)
    ) or 0

    average_interview_score = db.scalar(
        select(func.avg(InterviewSession.overall_score)).where(
            InterviewSession.student_id == student.id, InterviewSession.overall_score.is_not(None)
        )
    )

    latest_session = db.execute(
        select(InterviewSession.overall_score, InterviewSession.status)
        .where(InterviewSession.student_id == student.id)
        .order_by(InterviewSession.created_at.desc(), InterviewSession.id.desc())
        .limit(1)
    ).first()
    latest_interview_score = float(latest_session[0]) if latest_session and latest_session[0] is not None else None
    latest_interview_status = latest_session[1].value if latest_session else None

    resume_score = None
    if student.current_resume_id is not None:
        resume_score = db.scalar(
            select(ResumeAnalysis.overall_score)
            .where(ResumeAnalysis.resume_id == student.current_resume_id)
            .order_by(ResumeAnalysis.analyzed_at.desc(), ResumeAnalysis.id.desc())
            .limit(1)
        )

    return StudentAnalytics(
        total_applications=total_applications,
        applications_by_status=applications_by_status,
        open_jobs_count=open_jobs_count,
        recommended_jobs=recommended_jobs,
        total_interview_sessions=total_interview_sessions,
        questions_answered=questions_answered,
        average_interview_score=float(average_interview_score) if average_interview_score is not None else None,
        latest_interview_score=latest_interview_score,
        latest_interview_status=latest_interview_status,
        resume_score=resume_score,
    )


def get_recruiter_analytics(db: Session, recruiter: Recruiter) -> RecruiterAnalytics:
    # Every metric below is scoped to jobs whose company belongs to this
    # recruiter - a recruiter never sees another recruiter's data.
    base_job_filter = Job.company_id.in_(
        select(Company.id).where(Company.recruiter_id == recruiter.id)
    )

    total_jobs_posted = db.scalar(select(func.count()).select_from(Job).where(base_job_filter)) or 0
    active_jobs = db.scalar(
        select(func.count()).select_from(Job).where(base_job_filter, Job.status == JobStatus.OPEN)
    ) or 0
    closed_jobs = db.scalar(
        select(func.count()).select_from(Job).where(base_job_filter, Job.status == JobStatus.CLOSED)
    ) or 0
    jobs_linked_to_drives = db.scalar(
        select(func.count()).select_from(Job).where(base_job_filter, Job.placement_drive_id.is_not(None))
    ) or 0

    total_applications_received = db.scalar(
        select(func.count())
        .select_from(Application)
        .join(Job, Application.job_id == Job.id)
        .where(base_job_filter)
    ) or 0

    status_rows = db.execute(
        select(Application.status, func.count())
        .join(Job, Application.job_id == Job.id)
        .where(base_job_filter)
        .group_by(Application.status)
    ).all()
    applications_by_status = [StatusCount(status=s.value, count=c) for s, c in status_rows]

    applicant_rows = db.execute(
        select(Job.id, Job.title, func.count(Application.id))
        .outerjoin(Application, Application.job_id == Job.id)
        .where(base_job_filter)
        .group_by(Job.id, Job.title)
        .order_by(func.count(Application.id).desc())
    ).all()
    applicants_per_job = [
        JobApplicantCount(job_id=job_id, job_title=title, applicant_count=count)
        for job_id, title, count in applicant_rows
    ]

    return RecruiterAnalytics(
        total_jobs_posted=total_jobs_posted,
        active_jobs=active_jobs,
        closed_jobs=closed_jobs,
        total_applications_received=total_applications_received,
        applications_by_status=applications_by_status,
        applicants_per_job=applicants_per_job,
        jobs_linked_to_drives=jobs_linked_to_drives,
    )


def get_admin_analytics(db: Session) -> AdminAnalytics:
    total_students = db.scalar(select(func.count()).select_from(Student)) or 0
    total_recruiters = db.scalar(select(func.count()).select_from(Recruiter)) or 0
    total_companies = db.scalar(select(func.count()).select_from(Company)) or 0
    total_jobs = db.scalar(select(func.count()).select_from(Job)) or 0
    total_applications = db.scalar(select(func.count()).select_from(Application)) or 0

    applications_by_status = _status_counts(db, Application.status)
    jobs_by_status = _status_counts(db, Job.status)
    students_by_placement_status = _status_counts(db, Student.placement_status)

    selected_count = db.scalar(
        select(func.count())
        .select_from(Student)
        .where(Student.placement_status == PlacementStatus.SELECTED)
    ) or 0
    placement_percentage = round((selected_count / total_students) * 100, 2) if total_students else 0.0

    # Monthly application trend, last 6 calendar months - MySQL-specific
    # DATE_FORMAT is fine here since this project targets MySQL exclusively
    # (PyMySQL is a hard dependency throughout).
    month_expr = func.date_format(Application.created_at, "%Y-%m")
    trend_rows = db.execute(
        select(month_expr, func.count())
        .group_by(month_expr)
        .order_by(month_expr.desc())
        .limit(6)
    ).all()
    monthly_application_trend = [MonthCount(month=m, count=c) for m, c in trend_rows][::-1]

    return AdminAnalytics(
        total_students=total_students,
        total_recruiters=total_recruiters,
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
        applications_by_status=applications_by_status,
        jobs_by_status=jobs_by_status,
        students_by_placement_status=students_by_placement_status,
        placement_percentage=placement_percentage,
        monthly_application_trend=monthly_application_trend,
    )
