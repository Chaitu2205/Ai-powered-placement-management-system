from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.ai.answer_evaluator import AnswerEvaluatorProvider, get_answer_evaluator_provider
from app.ai.interview_generator import InterviewGeneratorProvider, get_interview_generator_provider
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.interview import (
    InterviewAnswerRead,
    InterviewAnswerSubmit,
    InterviewQuestionRead,
    InterviewSessionCreate,
    InterviewSessionRead,
)
from app.security.dependencies import require_role
from app.services import interview_service

router = APIRouter()


@router.post("", response_model=InterviewSessionRead, status_code=status.HTTP_201_CREATED)
def create_interview_session(
    payload: InterviewSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> InterviewSessionRead:
    """Starts a new interview practice session. job_id is optional (generic practice if omitted)."""
    return interview_service.create_session(db, current_user, payload)


@router.get("/my", response_model=list[InterviewSessionRead])
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> list:
    return interview_service.list_my_sessions(db, current_user)


@router.post("/{session_id}/generate-questions", response_model=list[InterviewQuestionRead])
def generate_questions(
    session_id: int,
    question_count: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    provider: InterviewGeneratorProvider = Depends(get_interview_generator_provider),
) -> list:
    """
    Generates and stores new questions for a session. Safe to call more than
    once - new questions are appended, not replacing prior ones.
    """
    return interview_service.generate_questions(
        db, current_user, session_id, provider, question_count=question_count
    )


@router.get("/{session_id}/questions", response_model=list[InterviewQuestionRead])
def list_questions(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT, UserRole.ADMIN)),
) -> list:
    return interview_service.list_questions(db, current_user, session_id)


@router.get("/{session_id}", response_model=InterviewSessionRead)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT, UserRole.ADMIN)),
) -> InterviewSessionRead:
    return interview_service.get_session(db, current_user, session_id)


@router.post("/questions/{question_id}/answer", response_model=InterviewAnswerRead, status_code=status.HTTP_201_CREATED)
def submit_answer(
    question_id: int,
    payload: InterviewAnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> InterviewAnswerRead:
    """Submits an answer to a question. One answer per question - resubmitting returns 409."""
    return interview_service.submit_answer(db, current_user, question_id, payload)


@router.post("/questions/{question_id}/evaluate", response_model=InterviewAnswerRead)
def evaluate_answer(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    provider: AnswerEvaluatorProvider = Depends(get_answer_evaluator_provider),
) -> InterviewAnswerRead:
    """
    Runs AI evaluation on the already-submitted answer and stores structured
    feedback. Safe to call again - re-evaluates and overwrites the feedback
    fields (unlike questions, an answer's evaluation isn't versioned
    history; it's a live judgment of the one stored answer).
    """
    return interview_service.evaluate_answer(db, current_user, question_id, provider)


@router.get("/questions/{question_id}/answer", response_model=InterviewAnswerRead)
def get_answer(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT, UserRole.ADMIN)),
) -> InterviewAnswerRead:
    return interview_service.get_answer(db, current_user, question_id)
