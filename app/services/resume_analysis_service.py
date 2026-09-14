"""
Resume analysis business logic.

Ownership/authorization is deliberately reused from `resume_service.get_resume`
rather than reimplemented: that function already enforces "owner student or
admin only" (recruiters excluded), which is exactly the rule Phase 7 needs -
one source of truth for "who can see this resume" instead of two.
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.resume_analyzer import ResumeAnalyzerProvider
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.services.resume_service import get_resume
from app.utils.exceptions import AppException, NotFoundError
from fastapi import status as http_status

logger = logging.getLogger("app")


def analyze_resume(
    db: Session, current_user: User, resume_id: int, provider: ResumeAnalyzerProvider
) -> ResumeAnalysis:
    """
    Runs AI analysis on a resume's extracted text and stores the result as a
    NEW ResumeAnalysis row (history is preserved, never overwritten - see
    the model's own docstring from Phase 2).
    """
    resume = get_resume(db, current_user, resume_id)  # raises 404/403 as appropriate

    if not resume.extracted_text or not resume.extracted_text.strip():
        raise AppException(
            "This resume has no extractable text. Try re-uploading a text-based PDF or DOCX.",
            status_code=http_status.HTTP_400_BAD_REQUEST,
        )

    result = provider.analyze(resume.extracted_text)

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        extracted_name=result.extracted_name,
        extracted_email=result.extracted_email,
        extracted_phone=result.extracted_phone,
        education_json=result.education,
        projects_json=result.projects,
        internships_json=result.internships,
        certifications_json=result.certifications,
        experience_json=result.experience,
        detected_skills_json=result.detected_skills,
        overall_score=result.overall_score,
        strengths_json=result.strengths,
        weaknesses_json=result.weaknesses,
        missing_skills_json=result.missing_skills,
        suggestions_json=result.suggestions,
        ats_keywords_json=result.ats_keywords,
        summary_text=result.summary,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_latest_analysis(db: Session, current_user: User, resume_id: int) -> ResumeAnalysis:
    """Returns the most recent analysis for a resume. Same ownership rule as analyze_resume."""
    get_resume(db, current_user, resume_id)  # ownership check; raises 404/403 as appropriate

    analysis = db.execute(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.resume_id == resume_id)
        # analyzed_at alone isn't a reliable ordering key: MySQL's DATETIME
        # defaults to whole-second precision, so two analyses created within
        # the same second (as happens in fast automated tests, and can
        # happen in production under quick repeated requests) get identical
        # timestamps, making ORDER BY analyzed_at DESC non-deterministic.
        # id is autoincrement and monotonically increasing, so it's a safe,
        # deterministic tiebreaker for "most recent" without needing a
        # schema change (e.g. DATETIME(6)) or touching any other row.
        .order_by(ResumeAnalysis.analyzed_at.desc(), ResumeAnalysis.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    if analysis is None:
        raise NotFoundError("This resume has not been analyzed yet")
    return analysis
