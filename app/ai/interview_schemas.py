"""
Structured contract every interview-question-generation provider must
return. Same validation-boundary pattern as app/ai/schemas.py (Phase 7).
"""
from pydantic import BaseModel, Field

from app.models.enums import InterviewType


class GeneratedQuestion(BaseModel):
    question_text: str = Field(min_length=5)
    category: InterviewType


class AIInterviewQuestionSet(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1)


class AIAnswerEvaluationResult(BaseModel):
    """Structured contract every answer-evaluation provider must return (Phase 10)."""

    score: float = Field(ge=0, le=10)
    relevance_score: float = Field(ge=0, le=10)
    correctness_score: float = Field(ge=0, le=10)
    completeness_score: float = Field(ge=0, le=10)
    communication_score: float = Field(ge=0, le=10)
    good_points: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    suggested_answer: str = ""
    feedback_summary: str = ""
