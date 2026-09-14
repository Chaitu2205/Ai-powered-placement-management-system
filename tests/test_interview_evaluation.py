"""
Integration tests for Phase 10: interview answer submission and AI
evaluation. Uses MockAnswerEvaluatorProvider via dependency override - no
real AI call is ever made in these tests.

Run with:
    pytest tests/test_interview_evaluation.py -v
"""
import pytest

from app.ai.answer_evaluator import (
    AIAnswerEvaluationResult,
    MockAnswerEvaluatorProvider,
    get_answer_evaluator_provider,
)
from app.ai.interview_generator import MockInterviewGeneratorProvider, get_interview_generator_provider
from app.main import app
from tests.conftest import auth_header
from tests.test_interviews import _create_session


@pytest.fixture()
def use_mocks():
    app.dependency_overrides[get_interview_generator_provider] = lambda: MockInterviewGeneratorProvider()
    app.dependency_overrides[get_answer_evaluator_provider] = lambda: MockAnswerEvaluatorProvider()
    yield
    app.dependency_overrides.pop(get_interview_generator_provider, None)
    app.dependency_overrides.pop(get_answer_evaluator_provider, None)


def _create_session_with_questions(client, token, question_count=2):
    session = _create_session(client, token)
    resp = client.post(
        f"/api/v1/interviews/{session['id']}/generate-questions?question_count={question_count}",
        headers=auth_header(token),
    )
    assert resp.status_code == 200, resp.text
    return session, resp.json()


class TestSubmitAnswer:
    def test_student_can_submit_answer(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]

        resp = client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "I would use dependency injection to decouple the components."},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["answer_text"].startswith("I would use dependency injection")
        assert body["score"] is None  # not evaluated yet

    def test_cannot_submit_twice_to_same_question(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]

        first = client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "First answer."},
            headers=auth_header(student_token),
        )
        assert first.status_code == 201

        second = client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "Second attempt."},
            headers=auth_header(student_token),
        )
        assert second.status_code == 409

    def test_recruiter_cannot_submit_answer(self, client, student_token, recruiter_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]

        resp = client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "Trying to answer someone else's question."},
            headers=auth_header(recruiter_token),
        )
        assert resp.status_code == 403

    def test_student_cannot_answer_another_students_question(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]

        client.post(
            "/api/v1/auth/register",
            json={
                "email": "other-student-p10@example.com",
                "password": "StrongPass123",
                "role": "student",
                "full_name": "Other Student",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={"email": "other-student-p10@example.com", "password": "StrongPass123"},
        )
        other_token = other_login.json()["access_token"]

        resp = client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "Not my question."},
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403


class TestEvaluateAnswer:
    def test_evaluate_returns_structured_feedback(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]
        client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "A reasonably detailed answer with several relevant words."},
            headers=auth_header(student_token),
        )

        resp = client.post(
            f"/api/v1/interviews/questions/{question_id}/evaluate", headers=auth_header(student_token)
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert 0 <= body["score"] <= 10
        assert body["feedback_summary"]
        assert isinstance(body["good_points_json"], list)
        assert isinstance(body["improvements_json"], list)

    def test_evaluate_without_answer_returns_400(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]

        resp = client.post(
            f"/api/v1/interviews/questions/{question_id}/evaluate", headers=auth_header(student_token)
        )
        assert resp.status_code == 400

    def test_evaluate_without_ai_configured_returns_503(self, client, student_token, monkeypatch):
        # Only override the generator (needed to create questions), not the evaluator -
        # so evaluation hits the real get_answer_evaluator_provider with AI_API_KEY="".
        app.dependency_overrides[get_interview_generator_provider] = lambda: MockInterviewGeneratorProvider()
        try:
            _, questions = _create_session_with_questions(client, student_token, 1)
            question_id = questions[0]["id"]
            client.post(
                f"/api/v1/interviews/questions/{question_id}/answer",
                json={"answer_text": "Some answer."},
                headers=auth_header(student_token),
            )
            resp = client.post(
                f"/api/v1/interviews/questions/{question_id}/evaluate", headers=auth_header(student_token)
            )
            assert resp.status_code == 503
        finally:
            app.dependency_overrides.pop(get_interview_generator_provider, None)

    def test_session_overall_score_updates_after_all_questions_evaluated(self, client, student_token, use_mocks):
        session, questions = _create_session_with_questions(client, student_token, 2)

        for q in questions:
            client.post(
                f"/api/v1/interviews/questions/{q['id']}/answer",
                json={"answer_text": "An answer with a reasonable number of words in it for scoring."},
                headers=auth_header(student_token),
            )
            client.post(f"/api/v1/interviews/questions/{q['id']}/evaluate", headers=auth_header(student_token))

        detail = client.get(f"/api/v1/interviews/{session['id']}", headers=auth_header(student_token))
        assert detail.status_code == 200
        body = detail.json()
        assert body["overall_score"] is not None
        assert body["status"] == "completed"

    def test_recruiter_cannot_evaluate(self, client, student_token, recruiter_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]
        client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "Some answer."},
            headers=auth_header(student_token),
        )

        resp = client.post(
            f"/api/v1/interviews/questions/{question_id}/evaluate", headers=auth_header(recruiter_token)
        )
        assert resp.status_code == 403


class TestGetAnswer:
    def test_get_answer_returns_submitted_and_evaluated_data(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]
        client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "My answer text."},
            headers=auth_header(student_token),
        )
        client.post(f"/api/v1/interviews/questions/{question_id}/evaluate", headers=auth_header(student_token))

        resp = client.get(f"/api/v1/interviews/questions/{question_id}/answer", headers=auth_header(student_token))
        assert resp.status_code == 200
        assert resp.json()["answer_text"] == "My answer text."
        assert resp.json()["score"] is not None

    def test_get_answer_before_submission_returns_404(self, client, student_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]

        resp = client.get(f"/api/v1/interviews/questions/{question_id}/answer", headers=auth_header(student_token))
        assert resp.status_code == 404

    def test_admin_can_view_answer_but_recruiter_cannot(self, client, student_token, admin_token, recruiter_token, use_mocks):
        _, questions = _create_session_with_questions(client, student_token, 1)
        question_id = questions[0]["id"]
        client.post(
            f"/api/v1/interviews/questions/{question_id}/answer",
            json={"answer_text": "Answer for admin visibility test."},
            headers=auth_header(student_token),
        )

        admin_resp = client.get(f"/api/v1/interviews/questions/{question_id}/answer", headers=auth_header(admin_token))
        assert admin_resp.status_code == 200

        recruiter_resp = client.get(
            f"/api/v1/interviews/questions/{question_id}/answer", headers=auth_header(recruiter_token)
        )
        assert recruiter_resp.status_code == 403


class TestMockEvaluatorUnit:
    def test_mock_produces_valid_result(self):
        from app.models.enums import InterviewType

        provider = MockAnswerEvaluatorProvider()
        result = provider.evaluate(
            question_text="How would you design a scalable REST API?",
            category=InterviewType.TECHNICAL,
            answer_text="I would use pagination, caching, and horizontal scaling for the REST API design.",
        )
        assert isinstance(result, AIAnswerEvaluationResult)
        assert 0 <= result.score <= 10
        assert result.feedback_summary
