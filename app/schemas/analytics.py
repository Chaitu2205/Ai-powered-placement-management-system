from typing import Optional

from pydantic import BaseModel

from app.schemas.job_match import RecommendedJobRead


class StatusCount(BaseModel):
    status: str
    count: int


class MonthCount(BaseModel):
    month: str  # "YYYY-MM"
    count: int


class JobApplicantCount(BaseModel):
    job_id: int
    job_title: str
    applicant_count: int


class StudentAnalytics(BaseModel):
    total_applications: int
    applications_by_status: list[StatusCount]
    open_jobs_count: int
    recommended_jobs: list[RecommendedJobRead]
    total_interview_sessions: int
    questions_answered: int
    average_interview_score: Optional[float]
    latest_interview_score: Optional[float]
    latest_interview_status: Optional[str]
    resume_score: Optional[int]


class RecruiterAnalytics(BaseModel):
    total_jobs_posted: int
    active_jobs: int
    closed_jobs: int
    total_applications_received: int
    applications_by_status: list[StatusCount]
    applicants_per_job: list[JobApplicantCount]
    jobs_linked_to_drives: int


class AdminAnalytics(BaseModel):
    total_students: int
    total_recruiters: int
    total_companies: int
    total_jobs: int
    total_applications: int
    applications_by_status: list[StatusCount]
    jobs_by_status: list[StatusCount]
    students_by_placement_status: list[StatusCount]
    placement_percentage: float
    monthly_application_trend: list[MonthCount]
