from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.enums import (
    DifficultyLevel,
    ExperienceLevel,
    InterviewType,
    SessionStatus,
)
from app.schemas.common import ORMBase


class InterviewSessionCreate(BaseModel):
    job_id: Optional[int] = None
    interview_type: InterviewType
    difficulty: DifficultyLevel
    experience_level: ExperienceLevel


class InterviewQuestionRead(ORMBase):
    id: int
    session_id: int
    question_text: str
    category: InterviewType
    order_index: int


class InterviewAnswerSubmit(BaseModel):
    answer_text: str


class InterviewAnswerRead(ORMBase):
    id: int
    question_id: int
    answer_text: str
    # score fields are stored as Numeric(4,2) in the DB (precise decimal
    # storage is correct there), but the API response schema uses `float`
    # rather than `Decimal`: Pydantic v2 serializes Decimal to a JSON
    # *string* by default (to avoid float precision loss), which broke
    # numeric comparisons like `0 <= score <= 10` on the client side.
    # Typing these as float here makes Pydantic coerce the ORM's Decimal
    # value during validation, so the API returns real JSON numbers.
    score: Optional[float]
    relevance_score: Optional[float]
    correctness_score: Optional[float]
    completeness_score: Optional[float]
    communication_score: Optional[float]
    good_points_json: Optional[list] = None
    improvements_json: Optional[list] = None
    suggested_answer: Optional[str]
    feedback_summary: Optional[str] = None
    submitted_at: datetime


class InterviewSessionRead(ORMBase):
    id: int
    student_id: int
    job_id: Optional[int]
    interview_type: InterviewType
    difficulty: DifficultyLevel
    experience_level: ExperienceLevel
    status: SessionStatus
    overall_score: Optional[Decimal]
    created_at: datetime
