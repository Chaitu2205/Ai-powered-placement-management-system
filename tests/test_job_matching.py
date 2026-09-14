"""
Integration tests for Phase 8: deterministic job-student matching.

No AI provider involved at all - compute_match() is pure Python/SQL, so
these tests exercise the real logic end-to-end, not a mock.

Run with:
    pytest tests/test_job_matching.py -v
"""
from app.models.resume_analysis import ResumeAnalysis
from app.models.skill import Skill
from app.models.student import Student
from app.models.student_skill import StudentSkill
from tests.conftest import auth_header
from tests.test_core_placement import _create_company
from tests.test_resumes import _minimal_pdf_bytes


def _create_job_with_skills(client, recruiter_token, company_id, skill_names, title="Backend Role"):
    resp = client.post(
        "/api/v1/jobs",
        json={
            "title": title,
            "description": "A role requiring several specific technical skills.",
            "company_id": company_id,
            "required_skills": [{"skill_name": s, "is_mandatory": True} for s in skill_names],
        },
        headers=auth_header(recruiter_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _give_student_skills(db_session, student_user_email: str, skill_names: list[str]):
    from app.models.user import User

    student = (
        db_session.query(Student)
        .join(Student.user)
        .filter(User.email == student_user_email)
        .one()
    )
    for name in skill_names:
        skill = db_session.query(Skill).filter(Skill.name == name).one_or_none()
        if skill is None:
            skill = Skill(name=name)
            db_session.add(skill)
            db_session.flush()
        db_session.add(StudentSkill(student_id=student.id, skill_id=skill.id))
    db_session.commit()
    return student


class TestComputeMatch:
    def test_full_skill_match_scores_100(self, client, recruiter_token, student_token, db_session):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["Python", "FastAPI"])
        _give_student_skills(db_session, "student@example.com", ["Python", "FastAPI"])

        response = client.get(f"/api/v1/jobs/{job['id']}/match", headers=auth_header(student_token))
        assert response.status_code == 200
        body = response.json()
        assert body["match_score"] == 100
        assert set(body["matched_skills"]) == {"Python", "FastAPI"}
        assert body["missing_skills"] == []

    def test_partial_skill_match_scores_proportionally(self, client, recruiter_token, student_token, db_session):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["Python", "FastAPI", "SQL", "Docker"])
        _give_student_skills(db_session, "student@example.com", ["Python", "SQL"])

        response = client.get(f"/api/v1/jobs/{job['id']}/match", headers=auth_header(student_token))
        assert response.status_code == 200
        body = response.json()
        assert body["match_score"] == 50  # 2 of 4 required skills
        assert set(body["matched_skills"]) == {"Python", "SQL"}
        assert set(body["missing_skills"]) == {"FastAPI", "Docker"}

    def test_job_with_no_required_skills_scores_100(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], [])

        response = client.get(f"/api/v1/jobs/{job['id']}/match", headers=auth_header(student_token))
        assert response.status_code == 200
        assert response.json()["match_score"] == 100

    def test_matching_is_case_insensitive(self, client, recruiter_token, student_token, db_session):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["python"])
        _give_student_skills(db_session, "student@example.com", ["Python"])

        response = client.get(f"/api/v1/jobs/{job['id']}/match", headers=auth_header(student_token))
        assert response.json()["match_score"] == 100

    def test_resume_analysis_score_influences_match(self, client, recruiter_token, student_token, db_session):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["Python", "FastAPI"])
        student = _give_student_skills(db_session, "student@example.com", ["Python"])  # 1 of 2 = 50 skill score

        # Upload a resume and attach a resume_analysis row directly (bypassing
        # the AI call entirely - Phase 8 doesn't need to mock AI, it just
        # reads whatever overall_score is already stored).
        upload = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", _minimal_pdf_bytes(), "application/pdf")},
            headers=auth_header(student_token),
        )
        resume_id = upload.json()["id"]
        db_session.add(ResumeAnalysis(resume_id=resume_id, overall_score=90))
        db_session.commit()

        response = client.get(f"/api/v1/jobs/{job['id']}/match", headers=auth_header(student_token))
        body = response.json()
        # 0.8 * 50 (skill) + 0.2 * 90 (resume) = 58
        assert body["match_score"] == 58

    def test_recruiter_cannot_access_match_endpoint(self, client, recruiter_token):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["Python"])

        response = client.get(f"/api/v1/jobs/{job['id']}/match", headers=auth_header(recruiter_token))
        assert response.status_code == 403


class TestRecommendedJobs:
    def test_recommendations_sorted_best_match_first(self, client, recruiter_token, student_token, db_session):
        company = _create_company(client, recruiter_token)
        strong_job = _create_job_with_skills(
            client, recruiter_token, company["id"], ["Python"], title="Strong Match Job"
        )
        weak_job = _create_job_with_skills(
            client, recruiter_token, company["id"], ["Python", "Rust", "Go", "Kotlin"], title="Weak Match Job"
        )
        _give_student_skills(db_session, "student@example.com", ["Python"])

        response = client.get("/api/v1/jobs/recommended", headers=auth_header(student_token))
        assert response.status_code == 200
        results = response.json()
        job_ids_in_order = [r["job_id"] for r in results]
        assert job_ids_in_order.index(strong_job["id"]) < job_ids_in_order.index(weak_job["id"])

    def test_recommendations_exclude_closed_jobs(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job_with_skills(client, recruiter_token, company["id"], ["Python"])
        client.post(f"/api/v1/jobs/{job['id']}/close", headers=auth_header(recruiter_token))

        response = client.get("/api/v1/jobs/recommended", headers=auth_header(student_token))
        job_ids = [r["job_id"] for r in response.json()]
        assert job["id"] not in job_ids

    def test_recommendations_respect_limit(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        for i in range(3):
            _create_job_with_skills(client, recruiter_token, company["id"], ["Python"], title=f"Job {i}")

        response = client.get("/api/v1/jobs/recommended?limit=2", headers=auth_header(student_token))
        assert len(response.json()) == 2

    def test_recruiter_cannot_access_recommended_endpoint(self, client, recruiter_token):
        response = client.get("/api/v1/jobs/recommended", headers=auth_header(recruiter_token))
        assert response.status_code == 403
