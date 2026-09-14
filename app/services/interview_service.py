"""
Interview session business logic.

Ownership rule (consistent with resume_service/resume_analysis_service):
owner student or admin only. Recruiters are not granted access to a
student's interview practice sessions - there's no existing business rule
that would justify it, same reasoning as Phase 7's resume analysis.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.answer_evaluator import AnswerEvaluatorProvider
from app.ai.interview_generator import InterviewGeneratorProvider
from app.models.enums import SessionStatus, UserRole
from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession
from app.models.job import Job
from app.models.student import Student
from app.models.user import User
from app.schemas.interview import InterviewAnswerSubmit, InterviewSessionCreate
from app.services.student_service import get_student_by_user_id
from app.utils.exceptions import AppException, ConflictError, NotFoundError, PermissionDeniedError
from fastapi import status as http_status

DEFAULT_QUESTION_COUNT = 8
MAX_QUESTION_COUNT = 20


def create_session(db: Session, current_user: User, payload: InterviewSessionCreate) -> InterviewSession:
    student = get_student_by_user_id(db, current_user.id)

    if payload.job_id is not None and db.get(Job, payload.job_id) is None:
        raise NotFoundError("Job not found")

    session = InterviewSession(
        student_id=student.id,
        job_id=payload.job_id,
        interview_type=payload.interview_type,
        difficulty=payload.difficulty,
        experience_level=payload.experience_level,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, current_user: User, session_id: int) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None:
        raise NotFoundError("Interview session not found")

    if current_user.role == UserRole.ADMIN:
        return session

    if current_user.role == UserRole.STUDENT:
        student = db.execute(
            select(Student).where(Student.user_id == current_user.id)
        ).scalar_one_or_none()
        if student is not None and session.student_id == student.id:
            return session

    raise PermissionDeniedError("You do not have permission to view this interview session")


def list_my_sessions(db: Session, current_user: User) -> list[InterviewSession]:
    student = get_student_by_user_id(db, current_user.id)
    return list(
        db.execute(
            select(InterviewSession)
            .where(InterviewSession.student_id == student.id)
            .order_by(InterviewSession.created_at.desc())
        )
        .scalars()
        .all()
    )


def _resume_excerpt(session: InterviewSession) -> Optional[str]:
    student = session.student
    if student.current_resume is not None and student.current_resume.extracted_text:
        return student.current_resume.extracted_text
    return None


def generate_questions(
    db: Session,
    current_user: User,
    session_id: int,
    provider: InterviewGeneratorProvider,
    question_count: int = DEFAULT_QUESTION_COUNT,
) -> list[InterviewQuestion]:
    session = get_session(db, current_user, session_id)
    question_count = max(1, min(question_count, MAX_QUESTION_COUNT))

    job = session.job
    required_skills = [js.skill.name for js in job.job_skills] if job is not None else []

    result = provider.generate_questions(
        interview_type=session.interview_type,
        difficulty=session.difficulty,
        experience_level=session.experience_level,
        question_count=question_count,
        job_title=job.title if job is not None else None,
        job_description=job.description if job is not None else None,
        required_skills=required_skills,
        resume_excerpt=_resume_excerpt(session),
    )

    # Existing questions for this session (if re-generating) get appended
    # after, not replaced - a student re-rolling questions keeps their
    # history rather than silently losing previously-asked questions.
    existing_count = db.execute(
        select(InterviewQuestion).where(InterviewQuestion.session_id == session.id)
    ).scalars().all()
    start_index = len(existing_count)

    new_questions = []
    for i, generated in enumerate(result.questions):
        question = InterviewQuestion(
            session_id=session.id,
            question_text=generated.question_text,
            # Coerce to the session's own interview_type rather than trusting
            # the AI's echoed category verbatim - the session is the source
            # of truth for what kind of interview this is.
            category=session.interview_type,
            order_index=start_index + i,
        )
        db.add(question)
        new_questions.append(question)

    db.commit()
    for q in new_questions:
        db.refresh(q)
    return new_questions


def list_questions(db: Session, current_user: User, session_id: int) -> list[InterviewQuestion]:
    get_session(db, current_user, session_id)  # ownership check
    return list(
        db.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.order_index)
        )
        .scalars()
        .all()
    )


def _get_owned_question(db: Session, current_user: User, question_id: int) -> InterviewQuestion:
    """
    Ownership check for a single question: resolves through its parent
    session using the exact same rule as get_session (owner student or
    admin only) - one source of truth for "who can touch this interview
    content", same reasoning as resume_service.get_resume in Phase 6/7.
    """
    question = db.get(InterviewQuestion, question_id)
    if question is None:
        raise NotFoundError("Interview question not found")

    get_session(db, current_user, question.session_id)  # raises 404/403 as appropriate
    return question


def submit_answer(
    db: Session, current_user: User, question_id: int, payload: InterviewAnswerSubmit
) -> InterviewAnswer:
    question = _get_owned_question(db, current_user, question_id)

    if current_user.role != UserRole.STUDENT:
        raise PermissionDeniedError("Only the student who owns this interview session can submit an answer")

    existing = db.execute(
        select(InterviewAnswer).where(InterviewAnswer.question_id == question.id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("This question has already been answered")

    answer = InterviewAnswer(question_id=question.id, answer_text=payload.answer_text)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def _get_owned_answer(db: Session, current_user: User, question_id: int) -> InterviewAnswer:
    question = _get_owned_question(db, current_user, question_id)
    answer = db.execute(
        select(InterviewAnswer).where(InterviewAnswer.question_id == question.id)
    ).scalar_one_or_none()
    if answer is None:
        raise NotFoundError("No answer has been submitted for this question yet")
    return answer


def get_answer(db: Session, current_user: User, question_id: int) -> InterviewAnswer:
    return _get_owned_answer(db, current_user, question_id)


def _recompute_session_overall_score(db: Session, session: InterviewSession) -> None:
    """
    Averages the score of every evaluated answer in this session and stores
    it on the session row, so GET /interviews/{id} reflects current progress
    without recomputing it on every read. Marks the session COMPLETED once
    every question has an evaluated answer.
    """
    questions = db.execute(
        select(InterviewQuestion).where(InterviewQuestion.session_id == session.id)
    ).scalars().all()

    scored_answers = [
        q.answer.score for q in questions if q.answer is not None and q.answer.score is not None
    ]
    if scored_answers:
        session.overall_score = Decimal(str(round(sum(scored_answers) / len(scored_answers), 2)))

    if questions and len(scored_answers) == len(questions):
        session.status = SessionStatus.COMPLETED


def evaluate_answer(
    db: Session, current_user: User, question_id: int, provider: AnswerEvaluatorProvider
) -> InterviewAnswer:
    question = _get_owned_question(db, current_user, question_id)

    if current_user.role != UserRole.STUDENT:
        raise PermissionDeniedError("Only the student who owns this interview session can request evaluation")

    answer = db.execute(
        select(InterviewAnswer).where(InterviewAnswer.question_id == question.id)
    ).scalar_one_or_none()
    if answer is None:
        raise AppException(
            "Submit an answer before requesting evaluation", status_code=http_status.HTTP_400_BAD_REQUEST
        )

    result = provider.evaluate(
        question_text=question.question_text,
        category=question.category,
        answer_text=answer.answer_text,
    )

    answer.score = Decimal(str(result.score))
    answer.relevance_score = Decimal(str(result.relevance_score))
    answer.correctness_score = Decimal(str(result.correctness_score))
    answer.completeness_score = Decimal(str(result.completeness_score))
    answer.communication_score = Decimal(str(result.communication_score))
    answer.good_points_json = result.good_points
    answer.improvements_json = result.improvements
    answer.suggested_answer = result.suggested_answer
    answer.feedback_summary = result.feedback_summary

    _recompute_session_overall_score(db, question.session)

    db.commit()
    db.refresh(answer)
    return answer
