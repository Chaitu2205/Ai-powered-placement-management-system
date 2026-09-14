"""
Integration tests for Phase 9: AI interview question generation.

Uses MockInterviewGeneratorProvider via dependency override - no real AI
call is ever made in these tests.

Run with:
    pytest tests/test_interviews.py -v
"""
import pytest

from app.ai.interview_generator import (
    AIInterviewQuestionSet,
    GeneratedQuestion,
    MockInterviewGeneratorProvider,
    get_interview_generator_provider,
)
from app.main import app
from tests.conftest import auth_header
from tests.test_core_placement import _create_company


def _create_job_with_skills(client, recruiter_token, company_id, skill_names, title="ML Engineer"):
    resp = client.post(
        "/api/v1/jobs",
        json={
            "title": title,
            "description": "Role requiring strong fundamentals.",
            "company_id": company_id,
            "required_skills": [{"skill_name": s, "is_mandatory": True} for s in skill_names],
        },
        headers=auth_header(recruiter_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_session(client, token, interview_type="technical", difficulty="medium", experience_level="fresher", job_id=None):
    resp = client.post(
        "/api/v1/interviews",
        json={
            "interview_type": interview_type,
            "difficulty": difficulty,
            "experience_level": experience_level,
            "job_id": job_id,
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def use_mock_interview_provider():
    app.dependency_overrides[get_interview_generator_provider] = lambda: MockInterviewGeneratorProvider()
    yield
    app.dependency_overrides.pop(get_interview_generator_provider, None)


class TestCreateSession:
    def test_student_can_create_generic_session(self, client, student_token):
        session = _create_session(client, student_token)
        assert session["interview_type"] == "technical"
        assert session["status"] == "in_progress"
        assert session["job_id"] is None

    def test_session_with_nonexistent_job_returns_404(self, client, student_token):
        resp = client.post(
            "/api/v1/interviews",
            json={"interview_type": "hr", "difficulty": "easy", "experience_level": "fresher", "job_id": 999999},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 404

    def test_recruiter_cannot_create_session(self, client, recruiter_token):
        resp = client.post(
            "/api/v1/interviews",
            json={"interview_type": "technical", "difficulty": "easy", "experience_level": "fresher"},
            headers=auth_header(recruiter_token),
        )
        assert resp.status_code == 403


class TestGenerateQuestions:
    def test_generate_questions_with_mock_provider(self, client, student_token, use_mock_interview_provider):
        session = _create_session(client, student_token)
        resp = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions?question_count=5",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200, resp.text
        questions = resp.json()
        assert len(questions) == 5
        assert all(q["category"] == "technical" for q in questions)
        assert [q["order_index"] for q in questions] == [0, 1, 2, 3, 4]

    def test_regenerating_appends_rather_than_replaces(self, client, student_token, use_mock_interview_provider):
        session = _create_session(client, student_token)
        first = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions?question_count=3",
            headers=auth_header(student_token),
        ).json()
        second = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions?question_count=2",
            headers=auth_header(student_token),
        ).json()

        assert [q["order_index"] for q in second] == [3, 4]

        all_questions = client.get(
            f"/api/v1/interviews/{session['id']}/questions", headers=auth_header(student_token)
        ).json()
        assert len(all_questions) == 5
        assert len(first) + len(second) == len(all_questions)

    def test_questions_use_job_context_when_session_has_a_job(
        self, client, recruiter_token, student_token, use_mock_interview_provider
    ):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["Kubernetes"])
        session = _create_session(client, student_token, job_id=job["id"])

        resp = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions?question_count=1",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        assert "Kubernetes" in resp.json()[0]["question_text"]

    def test_generate_without_ai_configured_returns_503(self, client, student_token):
        # No dependency override - hits the real provider, AI_API_KEY="" in test env.
        session = _create_session(client, student_token)
        resp = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions", headers=auth_header(student_token)
        )
        assert resp.status_code == 503

    def test_question_count_is_clamped_by_query_validation(self, client, student_token, use_mock_interview_provider):
        session = _create_session(client, student_token)
        resp = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions?question_count=999",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 422  # Query(..., le=20) rejects it outright


class TestOwnershipAndAccess:
    def test_student_cannot_access_another_students_session(self, client, student_token, use_mock_interview_provider):
        session = _create_session(client, student_token)

        client.post(
            "/api/v1/auth/register",
            json={
                "email": "other-student-p9@example.com",
                "password": "StrongPass123",
                "role": "student",
                "full_name": "Other Student",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={"email": "other-student-p9@example.com", "password": "StrongPass123"},
        )
        other_token = other_login.json()["access_token"]

        resp = client.get(f"/api/v1/interviews/{session['id']}", headers=auth_header(other_token))
        assert resp.status_code == 403

    def test_admin_can_view_but_not_generate_for_a_students_session(
        self, client, student_token, admin_token, use_mock_interview_provider
    ):
        session = _create_session(client, student_token)
        client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions?question_count=2",
            headers=auth_header(student_token),
        )

        view_resp = client.get(f"/api/v1/interviews/{session['id']}", headers=auth_header(admin_token))
        assert view_resp.status_code == 200

        questions_resp = client.get(
            f"/api/v1/interviews/{session['id']}/questions", headers=auth_header(admin_token)
        )
        assert questions_resp.status_code == 200
        assert len(questions_resp.json()) == 2

        generate_resp = client.post(
            f"/api/v1/interviews/{session['id']}/generate-questions", headers=auth_header(admin_token)
        )
        assert generate_resp.status_code == 403  # admin can view, not generate

    def test_recruiter_cannot_view_session_or_questions(self, client, student_token, recruiter_token):
        session = _create_session(client, student_token)
        assert client.get(f"/api/v1/interviews/{session['id']}", headers=auth_header(recruiter_token)).status_code == 403
        assert (
            client.get(f"/api/v1/interviews/{session['id']}/questions", headers=auth_header(recruiter_token)).status_code
            == 403
        )

    def test_list_my_sessions_returns_only_own(self, client, student_token):
        _create_session(client, student_token)
        _create_session(client, student_token, interview_type="hr")

        resp = client.get("/api/v1/interviews/my", headers=auth_header(student_token))
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestMockProviderUnit:
    def test_mock_generates_requested_count_and_category(self):
        from app.models.enums import DifficultyLevel, ExperienceLevel, InterviewType

        provider = MockInterviewGeneratorProvider()
        result = provider.generate_questions(
            interview_type=InterviewType.BEHAVIORAL,
            difficulty=DifficultyLevel.HARD,
            experience_level=ExperienceLevel.EXPERIENCED,
            question_count=4,
            job_title="Backend Engineer",
            job_description=None,
            required_skills=[],
            resume_excerpt=None,
        )
        assert isinstance(result, AIInterviewQuestionSet)
        assert len(result.questions) == 4
        assert all(q.category == InterviewType.BEHAVIORAL for q in result.questions)
        assert all(isinstance(q, GeneratedQuestion) for q in result.questions)
