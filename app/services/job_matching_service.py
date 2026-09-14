"""
Job-to-student matching.

Deliberately deterministic: the match score is computed from actual
database facts (the student's recorded skills vs. a job's required
skills, plus their latest resume-analysis score if one exists) rather than
sent to an LLM. This keeps matching fast, explainable, reproducible, and
free of AI cost/latency/failure modes for something that's fundamentally a
set-comparison problem. Nothing here is an AI call.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import JobStatus
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.resume_analysis import ResumeAnalysis
from app.models.student import Student
from app.schemas.job_match import JobMatchRead, RecommendedJobRead

# Skill-match makes up most of the score; a recent resume-analysis score (if
# one exists) nudges it up or down slightly to reward an otherwise
# well-put-together resume.
_SKILL_WEIGHT = 0.8
_RESUME_WEIGHT = 0.2


def _student_skill_names(student: Student) -> set[str]:
    return {link.skill.name.strip().lower() for link in student.student_skills}


def _job_required_skills(job: Job) -> list[JobSkill]:
    return list(job.job_skills)


def _latest_resume_analysis_score(db: Session, student: Student) -> Optional[int]:
    if student.current_resume_id is None:
        return None
    analysis = db.execute(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.resume_id == student.current_resume_id)
        .order_by(ResumeAnalysis.analyzed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return analysis.overall_score if analysis else None


def _recommendation_text(score: int, matched: list[str], missing: list[str]) -> str:
    if score >= 80:
        tier = "Strong match."
    elif score >= 60:
        tier = "Good match."
    elif score >= 40:
        tier = "Moderate match."
    else:
        tier = "Weak match."

    parts = [tier]
    if matched:
        parts.append(f"Matches on: {', '.join(matched)}.")
    if missing:
        parts.append(f"Consider strengthening: {', '.join(missing)}.")
    return " ".join(parts)


def compute_match(db: Session, student: Student, job: Job) -> JobMatchRead:
    student_skills = _student_skill_names(student)
    required = _job_required_skills(job)

    matched = sorted(
        {js.skill.name for js in required if js.skill.name.strip().lower() in student_skills}
    )
    missing = sorted(
        {js.skill.name for js in required if js.skill.name.strip().lower() not in student_skills}
    )

    skill_score = 100.0 if not required else (len(matched) / len(required)) * 100.0

    resume_score = _latest_resume_analysis_score(db, student)
    if resume_score is not None:
        final_score = (skill_score * _SKILL_WEIGHT) + (resume_score * _RESUME_WEIGHT)
    else:
        final_score = skill_score

    final_score_int = round(max(0.0, min(100.0, final_score)))

    return JobMatchRead(
        job_id=job.id,
        job_title=job.title,
        match_score=final_score_int,
        matched_skills=matched,
        missing_skills=missing,
        recommendation=_recommendation_text(final_score_int, matched, missing),
    )


def get_recommended_jobs(db: Session, student: Student, limit: int = 10) -> list[RecommendedJobRead]:
    """Ranks all currently-open jobs for this student, best match first."""
    open_jobs = list(
        db.execute(
            select(Job)
            .where(Job.status == JobStatus.OPEN)
            .options(selectinload(Job.job_skills).selectinload(JobSkill.skill), selectinload(Job.company))
        )
        .scalars()
        .all()
    )

    ranked = []
    for job in open_jobs:
        match = compute_match(db, student, job)
        ranked.append(
            RecommendedJobRead(
                **match.model_dump(),
                company_name=job.company.name,
            )
        )

    ranked.sort(key=lambda r: r.match_score, reverse=True)
    return ranked[:limit]
