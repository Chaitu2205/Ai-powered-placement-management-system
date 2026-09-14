"""
Integration tests for Phase 7: AI resume analysis.

These tests NEVER call a real AI provider - they override the
`get_resume_analyzer_provider` FastAPI dependency with
`MockResumeAnalyzerProvider` (deterministic, keyword-based, no network),
the same dependency-override pattern this project already uses for `get_db`.

Run with:
    pytest tests/test_resume_analysis.py -v
"""
import pytest

from app.ai.exceptions import AIResponseValidationError
from app.ai.resume_analyzer import (
    AIResumeAnalysisResult,
    MockResumeAnalyzerProvider,
    ResumeAnalyzerProvider,
    _parse_and_validate,
    get_resume_analyzer_provider,
)
from app.main import app
from tests.conftest import auth_header
from tests.test_resumes import _minimal_pdf_bytes


def _upload_resume(client, token, text="Experienced Python and FastAPI developer with Docker skills"):
    pdf_bytes = _minimal_pdf_bytes(text)
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=auth_header(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture()
def use_mock_ai_provider():
    """Overrides the AI provider dependency with the deterministic mock for the duration of a test."""
    app.dependency_overrides[get_resume_analyzer_provider] = lambda: MockResumeAnalyzerProvider()
    yield
    app.dependency_overrides.pop(get_resume_analyzer_provider, None)


class TestAnalyzeResume:
    def test_analyze_with_mock_provider_succeeds(self, client, student_token, use_mock_ai_provider):
        resume_id = _upload_resume(client, student_token)

        response = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(student_token))
        assert response.status_code == 201, response.text
        body = response.json()
        assert "python" in body["detected_skills_json"]
        assert "fastapi" in body["detected_skills_json"]
        assert 0 <= body["overall_score"] <= 100
        assert body["summary_text"]

    def test_get_latest_analysis_returns_most_recent(self, client, student_token, use_mock_ai_provider):
        resume_id = _upload_resume(client, student_token)

        first = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(student_token))
        second = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(student_token))
        assert first.json()["id"] != second.json()["id"]

        latest = client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=auth_header(student_token))
        assert latest.status_code == 200
        assert latest.json()["id"] == second.json()["id"]

    def test_get_analysis_before_any_run_returns_404(self, client, student_token):
        resume_id = _upload_resume(client, student_token)
        response = client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=auth_header(student_token))
        assert response.status_code == 404

    def test_analyze_with_no_extractable_text_returns_400(self, client, student_token, db_session, use_mock_ai_provider):
        from app.models.resume import Resume

        resume_id = _upload_resume(client, student_token)
        resume = db_session.get(Resume, resume_id)
        resume.extracted_text = ""
        db_session.commit()

        response = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(student_token))
        assert response.status_code == 400

    def test_analyze_without_ai_configured_returns_503(self, client, student_token):
        # No dependency override here - hits the real get_resume_analyzer_provider,
        # which sees AI_API_KEY="" (set in conftest for the whole test session)
        # and must fail cleanly, not crash.
        resume_id = _upload_resume(client, student_token)
        response = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(student_token))
        assert response.status_code == 503


class TestAnalysisAuthorization:
    def test_recruiter_cannot_analyze_or_view_analysis(self, client, student_token, recruiter_token, use_mock_ai_provider):
        resume_id = _upload_resume(client, student_token)
        client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(student_token))

        analyze_resp = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(recruiter_token))
        assert analyze_resp.status_code == 403

        view_resp = client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=auth_header(recruiter_token))
        assert view_resp.status_code == 403

    def test_student_cannot_analyze_another_students_resume(self, client, student_token, use_mock_ai_provider):
        resume_id = _upload_resume(client, student_token)

        client.post(
            "/api/v1/auth/register",
            json={
                "email": "other-student-p7@example.com",
                "password": "StrongPass123",
                "role": "student",
                "full_name": "Other Student",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={"email": "other-student-p7@example.com", "password": "StrongPass123"},
        )
        other_token = other_login.json()["access_token"]

        response = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(other_token))
        assert response.status_code == 403

    def test_admin_can_analyze_and_view_any_resume(self, client, student_token, admin_token, use_mock_ai_provider):
        resume_id = _upload_resume(client, student_token)

        analyze_resp = client.post(f"/api/v1/resumes/{resume_id}/analyze", headers=auth_header(admin_token))
        assert analyze_resp.status_code == 201

        view_resp = client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=auth_header(admin_token))
        assert view_resp.status_code == 200


class TestMockProvider:
    """Unit tests for the mock provider itself - no HTTP, no DB."""

    def test_detects_known_skills(self):
        provider = MockResumeAnalyzerProvider()
        result = provider.analyze("I have 3 years of experience with Python and SQL.")
        assert "python" in result.detected_skills
        assert "sql" in result.detected_skills
        assert isinstance(result, AIResumeAnalysisResult)

    def test_score_is_within_bounds(self):
        provider = MockResumeAnalyzerProvider()
        result = provider.analyze("Python FastAPI SQL React JavaScript Docker AWS Git")
        assert 0 <= result.overall_score <= 100


class TestResponseParsing:
    """Unit tests for the JSON parsing/validation boundary between the LLM and our schema."""

    def test_valid_json_parses(self):
        raw = (
            '{"extracted_name": "Jane Doe", "extracted_email": null, "extracted_phone": null, '
            '"education": [], "projects": [], "internships": [], "certifications": [], '
            '"experience": [], "detected_skills": ["python"], "missing_skills": [], '
            '"ats_keywords": [], "strengths": [], "weaknesses": [], "suggestions": [], '
            '"overall_score": 75, "summary": "Solid candidate."}'
        )
        result = _parse_and_validate(raw)
        assert result.extracted_name == "Jane Doe"
        assert result.overall_score == 75

    def test_markdown_fenced_json_is_stripped_and_parses(self):
        raw = '```json\n{"overall_score": 60, "summary": "ok"}\n```'
        result = _parse_and_validate(raw)
        assert result.overall_score == 60

    def test_garbage_response_raises_validation_error(self):
        with pytest.raises(AIResponseValidationError):
            _parse_and_validate("this is not json at all")

    def test_json_missing_required_field_raises_validation_error(self):
        # overall_score is required (no default) - omitting it must fail validation.
        with pytest.raises(AIResponseValidationError):
            _parse_and_validate('{"summary": "no score provided"}')
