"""
AI provider abstraction for resume analysis.

    api/v1/resumes.py  ->  services/resume_analysis_service.py  ->  THIS MODULE  ->  LLM provider

Anything that calls an LLM lives here and nowhere else. The API key is read
from settings (env var) and never touches the frontend. `get_resume_analyzer_provider`
is a FastAPI dependency, which is what makes it trivial for tests to swap in
`MockResumeAnalyzerProvider` via `app.dependency_overrides` - the same
pattern already used for `get_db` in this project's tests.
"""
import json
import logging
from abc import ABC, abstractmethod

from pydantic import ValidationError

from app.ai.exceptions import AIConfigurationError, AIProviderError, AIResponseValidationError
from app.ai.schemas import AIResumeAnalysisResult
from app.config.settings import get_settings

logger = logging.getLogger("app")

_SYSTEM_PROMPT = """You are a resume analysis engine for a placement management system.
Given the raw text extracted from a candidate's resume, analyze it and respond with ONLY a
single JSON object - no markdown fences, no commentary before or after - matching exactly
this shape:

{
  "extracted_name": string or null,
  "extracted_email": string or null,
  "extracted_phone": string or null,
  "education": [string],
  "projects": [string],
  "internships": [string],
  "certifications": [string],
  "experience": [string],
  "detected_skills": [string],
  "missing_skills": [string],
  "ats_keywords": [string],
  "strengths": [string],
  "weaknesses": [string],
  "suggestions": [string],
  "overall_score": integer from 0 to 100,
  "summary": string
}

Be honest and specific. Do not invent experience or skills that aren't evidenced in the text.
If the resume text is too sparse to assess something, use an empty list or null rather than
guessing."""


class ResumeAnalyzerProvider(ABC):
    """Interface every resume-analysis provider (real or mock) must implement."""

    @abstractmethod
    def analyze(self, resume_text: str) -> AIResumeAnalysisResult:
        raise NotImplementedError


class AnthropicResumeAnalyzer(ResumeAnalyzerProvider):
    """
    Production provider - calls the Anthropic Messages API.

    NOTE: this has not been exercised against a live API in development
    (no network access in the environment this was built in). The request/
    response handling follows the documented `anthropic` SDK usage; please
    verify with a real API key before relying on it in production.
    """

    def __init__(self, api_key: str, model_name: str):
        self._api_key = api_key
        self._model_name = model_name
        self._client = None  # created lazily, see _get_client

    def _get_client(self):
        if self._client is None:
            import anthropic  # imported lazily so a missing package doesn't break app startup
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def analyze(self, resume_text: str) -> AIResumeAnalysisResult:
        client = self._get_client()

        try:
            response = client.messages.create(
                model=self._model_name,
                max_tokens=2000,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Resume text:\n\n{resume_text}"}],
            )
        except Exception as exc:  # network error, auth error, rate limit, timeout, etc.
            logger.error("Anthropic resume analysis call failed: %s", exc)
            raise AIProviderError() from exc

        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()

        return _parse_and_validate(raw_text)


class MockResumeAnalyzerProvider(ResumeAnalyzerProvider):
    """
    TEST-ONLY deterministic provider. Never used in production - production
    routes always resolve `get_resume_analyzer_provider()`, which only ever
    returns `AnthropicResumeAnalyzer`. Tests override the dependency
    explicitly with this class via `app.dependency_overrides`.

    Uses simple keyword matching (no LLM call at all) so tests are fast,
    deterministic, and don't require network access or an API key.
    """

    _KNOWN_SKILLS = [
        "python", "fastapi", "sql", "react", "javascript", "docker",
        "aws", "sqlalchemy", "git", "rest api", "machine learning",
    ]

    def analyze(self, resume_text: str) -> AIResumeAnalysisResult:
        lowered = resume_text.lower()
        detected = [skill for skill in self._KNOWN_SKILLS if skill in lowered]
        missing = [skill for skill in ("docker", "aws") if skill not in detected]

        return AIResumeAnalysisResult(
            detected_skills=detected,
            missing_skills=missing,
            strengths=["Relevant technical skills present"] if detected else [],
            weaknesses=["Resume text is very short"] if len(resume_text.split()) < 20 else [],
            suggestions=["Add measurable outcomes to project descriptions"],
            ats_keywords=detected,
            overall_score=min(100, 40 + len(detected) * 10),
            summary=f"Candidate resume mentioning {len(detected)} recognized skill(s).",
        )


def _parse_and_validate(raw_text: str) -> AIResumeAnalysisResult:
    # Defensive: strip a markdown code fence if the model added one despite instructions.
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
        return AIResumeAnalysisResult.model_validate(parsed)
    except ValidationError as exc:
        logger.error("AI response failed schema validation: %s", exc)
        raise AIResponseValidationError() from exc


def get_resume_analyzer_provider() -> ResumeAnalyzerProvider:
    """
    FastAPI dependency. Always returns the real provider - there is no
    environment-based switch to the mock, by design (rule: never let a mock
    silently run in production). Raises AIConfigurationError (503) if
    AI_API_KEY isn't set, rather than failing at import/startup time.
    """
    settings = get_settings()
    if not settings.AI_API_KEY:
        raise AIConfigurationError(
            "AI_API_KEY is not configured. Set it in your .env to enable resume analysis."
        )
    return AnthropicResumeAnalyzer(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL_NAME)
