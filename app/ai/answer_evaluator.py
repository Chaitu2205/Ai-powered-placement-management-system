"""
AI provider abstraction for interview answer evaluation.

    api/v1/interviews.py -> services/interview_service.py -> THIS MODULE -> LLM provider

Same shape as app/ai/resume_analyzer.py (Phase 7) and app/ai/interview_generator.py
(Phase 9): abstract provider interface, a real Anthropic-backed implementation,
and a test-only mock swapped in via `app.dependency_overrides`.
"""
import json
import logging
from abc import ABC, abstractmethod

from pydantic import ValidationError

from app.ai.exceptions import AIConfigurationError, AIProviderError, AIResponseValidationError
from app.ai.interview_schemas import AIAnswerEvaluationResult
from app.config.settings import get_settings
from app.models.enums import InterviewType

logger = logging.getLogger("app")


class AnswerEvaluatorProvider(ABC):
    @abstractmethod
    def evaluate(
        self, *, question_text: str, category: InterviewType, answer_text: str
    ) -> AIAnswerEvaluationResult:
        raise NotImplementedError


_SYSTEM_PROMPT = """You are an interview-answer evaluator for a placement management platform.
Given an interview question, its category, and a candidate's answer, evaluate the answer.

For "technical" questions, weight technical correctness heavily.
For "hr" or "behavioral" questions, weight relevance, clarity, structure, professionalism, and
completeness rather than technical correctness.

Respond with ONLY a single JSON object - no markdown fences, no commentary - matching exactly:

{
  "score": number 0-10,
  "relevance_score": number 0-10,
  "correctness_score": number 0-10,
  "completeness_score": number 0-10,
  "communication_score": number 0-10,
  "good_points": [string],
  "improvements": [string],
  "suggested_answer": string,
  "feedback_summary": string (2-3 sentences, written directly to the candidate)
}

Be constructive and specific. Do not be needlessly harsh, but do not inflate scores either."""


class AnthropicAnswerEvaluator(AnswerEvaluatorProvider):
    """
    Production provider - calls the Anthropic Messages API.

    NOTE: not exercised against a live API in development (no network
    access in the environment this was built in). Follows the documented
    `anthropic` SDK usage; verify with a real API key before relying on it.
    """

    def __init__(self, api_key: str, model_name: str):
        self._api_key = api_key
        self._model_name = model_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def evaluate(
        self, *, question_text: str, category: InterviewType, answer_text: str
    ) -> AIAnswerEvaluationResult:
        client = self._get_client()
        user_content = (
            f"Category: {category.value}\nQuestion: {question_text}\nCandidate's answer: {answer_text}"
        )

        try:
            response = client.messages.create(
                model=self._model_name,
                max_tokens=1500,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
        except Exception as exc:
            logger.error("Anthropic answer evaluation call failed: %s", exc)
            raise AIProviderError() from exc

        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        return _parse_and_validate(raw_text)


class MockAnswerEvaluatorProvider(AnswerEvaluatorProvider):
    """
    TEST-ONLY deterministic provider. Never used in production - production
    routes always resolve `get_answer_evaluator_provider()`, which only
    returns `AnthropicAnswerEvaluator`. Tests override the dependency
    explicitly with this class.

    Simple heuristic (word count + keyword overlap with the question) - no
    network, fully deterministic, fast.
    """

    def evaluate(
        self, *, question_text: str, category: InterviewType, answer_text: str
    ) -> AIAnswerEvaluationResult:
        word_count = len(answer_text.split())
        question_keywords = {w.lower().strip("?,.") for w in question_text.split() if len(w) > 4}
        answer_words = {w.lower().strip("?,.") for w in answer_text.split()}
        overlap = len(question_keywords & answer_words)

        completeness = min(10.0, word_count / 8)
        relevance = min(10.0, 4.0 + overlap * 2.0)
        base_score = round((completeness + relevance) / 2, 1)

        good_points = ["Answer addresses the question directly"] if overlap > 0 else []
        improvements = ["Provide more specific detail"] if word_count < 20 else []

        return AIAnswerEvaluationResult(
            score=base_score,
            relevance_score=relevance,
            correctness_score=base_score,
            completeness_score=completeness,
            communication_score=min(10.0, 5.0 + word_count / 20),
            good_points=good_points,
            improvements=improvements,
            suggested_answer="A strong answer would directly reference the question's key terms and give a concrete example.",
            feedback_summary=f"Your answer used {word_count} words with {overlap} relevant keyword(s) from the question.",
        )


def _parse_and_validate(raw_text: str) -> AIAnswerEvaluationResult:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("AI response was not valid JSON: %s", raw_text[:500])
        raise AIResponseValidationError() from exc

    try:
        return AIAnswerEvaluationResult.model_validate(parsed)
    except ValidationError as exc:
        logger.error("AI response failed schema validation: %s", exc)
        raise AIResponseValidationError() from exc


def get_answer_evaluator_provider() -> AnswerEvaluatorProvider:
    """
    FastAPI dependency. Always the real provider in production - raises
    AIConfigurationError (503) if AI_API_KEY isn't set, rather than failing
    at import/startup time.
    """
    settings = get_settings()
    if not settings.AI_API_KEY:
        raise AIConfigurationError(
            "AI_API_KEY is not configured. Set it in your .env to enable answer evaluation."
        )
    return AnthropicAnswerEvaluator(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL_NAME)
