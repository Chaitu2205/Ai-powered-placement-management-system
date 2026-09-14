"""
Central place where every /api/v1/* router is registered.

main.py includes this router under the configured API_V1_PREFIX, so each
phase only needs to add an `api_router.include_router(...)` line here - no
changes to main.py are required.
"""
from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    applications,
    auth,
    audit_logs,
    companies,
    departments,
    drives,
    interviews,
    jobs,
    notifications,
    recruiters,
    resumes,
    skills,
    students,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(recruiters.router, prefix="/recruiters", tags=["Recruiters"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(drives.router, prefix="/drives", tags=["Placement Drives"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
