"""
AI provider abstraction for interview question generation.

    api/v1/interviews.py -> services/interview_service.py -> THIS MODULE -> LLM provider

Same shape as app/ai/resume_analyzer.py (Phase 7): an abstract provider
interface, a real Anthropic-backed implementation, and a test-only mock -
swapped in tests via the same `app.dependency_overrides` mechanism.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import ValidationError

from app.ai.exceptions import AIConfigurationError, AIProviderError, AIResponseValidationError
from app.ai.interview_schemas import AIInterviewQuestionSet, GeneratedQuestion
from app.config.settings import get_settings
from app.models.enums import DifficultyLevel, ExperienceLevel, InterviewType

logger = logging.getLogger("app")


class InterviewGeneratorProvider(ABC):
    @abstractmethod
    def generate_questions(
        self,
        *,
        interview_type: InterviewType,
        difficulty: DifficultyLevel,
        experience_level: ExperienceLevel,
        question_count: int,
        job_title: Optional[str],
        job_description: Optional[str],
        required_skills: list[str],
        resume_excerpt: Optional[str],
    ) -> AIInterviewQuestionSet:
        raise NotImplementedError


def _build_prompt(
    *,
    interview_type: InterviewType,
    difficulty: DifficultyLevel,
    experience_level: ExperienceLevel,
    question_count: int,
    job_title: Optional[str],
    job_description: Optional[str],
    required_skills: list[str],
    resume_excerpt: Optional[str],
) -> str:
    context_lines = [
        f"Interview category: {interview_type.value}",
        f"Difficulty: {difficulty.value}",
        f"Candidate experience level: {experience_level.value}",
        f"Number of questions required: {question_count}",
    ]
    if job_title:
        context_lines.append(f"Job title: {job_title}")
    if job_description:
        context_lines.append(f"Job description: {job_description}")
    if required_skills:
        context_lines.append(f"Required skills: {', '.join(required_skills)}")
    if resume_excerpt:
        context_lines.append(f"Candidate resume excerpt: {resume_excerpt[:2000]}")

    return "\n".join(context_lines)


_SYSTEM_PROMPT = """You are an interview-question generator for a placement management platform.
Given the context below, generate exactly the requested number of interview questions, all
belonging to the specified category (technical, hr, or behavioral), at the specified difficulty,
appropriate for the candidate's experience level. Where a job title/description/required skills
or resume excerpt are provided, make questions specific and relevant to them rather than generic.

Respond with ONLY a single JSON object - no markdown fences, no commentary - matching exactly:

{"questions": [{"question_text": string, "category": "technical" | "hr" | "behavioral"}]}

Every question's "category" must equal the requested category exactly."""


class AnthropicInterviewGenerator(InterviewGeneratorProvider):
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

    def generate_questions(self, **kwargs) -> AIInterviewQuestionSet:
        client = self._get_client()
        prompt = _build_prompt(**kwargs)

        try:
            response = client.messages.create(
                model=self._model_name,
                max_tokens=2000,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            logger.error("Anthropic interview generation call failed: %s", exc)
            raise AIProviderError() from exc

        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        return _parse_and_validate(raw_text)


class MockInterviewGeneratorProvider(InterviewGeneratorProvider):
    """
    TEST-ONLY deterministic provider. Never used in production - production
    routes always resolve `get_interview_generator_provider()`, which only
    returns `AnthropicInterviewGenerator`. Tests override the dependency
    explicitly with this class.
    """

    _TEMPLATES = {
        InterviewType.TECHNICAL: "Explain how you would approach {topic} in a production system.",
        InterviewType.HR: "Why do you want to work in this role, in the context of {topic}?",
        InterviewType.BEHAVIORAL: "Tell me about a time you dealt with a challenge related to {topic}.",
    }

    def generate_questions(
        self,
        *,
        interview_type: InterviewType,
        difficulty: DifficultyLevel,
        experience_level: ExperienceLevel,
        question_count: int,
        job_title: Optional[str],
        job_description: Optional[str],
        required_skills: list[str],
        resume_excerpt: Optional[str],
    ) -> AIInterviewQuestionSet:
        template = self._TEMPLATES[interview_type]
        topics = required_skills[:question_count] or [job_title or "your recent experience"]
        # Pad by cycling topics if there are fewer topics than questions requested.
        while len(topics) < question_count:
            topics.append(topics[len(topics) % max(len(topics), 1)] if topics else "your experience")

        questions = [
            GeneratedQuestion(question_text=template.format(topic=topics[i]), category=interview_type)
            for i in range(question_count)
        ]
        return AIInterviewQuestionSet(questions=questions)


def _parse_and_validate(raw_text: str) -> AIInterviewQuestionSet:
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
        return AIInterviewQuestionSet.model_validate(parsed)
    except ValidationError as exc:
        logger.error("AI response failed schema validation: %s", exc)
        raise AIResponseValidationError() from exc


def get_interview_generator_provider() -> InterviewGeneratorProvider:
    """
    FastAPI dependency. Always the real provider in production - raises
    AIConfigurationError (503) if AI_API_KEY isn't set, rather than failing
    at import/startup time.
    """
    settings = get_settings()
    if not settings.AI_API_KEY:
        raise AIConfigurationError(
            "AI_API_KEY is not configured. Set it in your .env to enable interview generation."
        )
    return AnthropicInterviewGenerator(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL_NAME)
