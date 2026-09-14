"""
Integration tests for Phase 4: students, companies, jobs, applications.

Run with:
    pytest tests/test_core_placement.py -v
"""
from tests.conftest import auth_header


def _create_company(client, recruiter_token, name="Acme Corp"):
    resp = client.post(
        "/api/v1/companies",
        json={"name": name, "industry": "Software"},
        headers=auth_header(recruiter_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_job(client, recruiter_token, company_id, title="Python Developer"):
    resp = client.post(
        "/api/v1/jobs",
        json={
            "title": title,
            "description": "Looking for a Python developer with FastAPI and SQL experience.",
            "company_id": company_id,
            "required_skills": [
                {"skill_name": "Python", "is_mandatory": True},
                {"skill_name": "FastAPI", "is_mandatory": True},
            ],
        },
        headers=auth_header(recruiter_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestStudentProfile:
    def test_get_and_update_own_profile(self, client, student_token):
        me = client.get("/api/v1/students/me", headers=auth_header(student_token))
        assert me.status_code == 200
        assert me.json()["full_name"] == "Test Student"

        updated = client.put(
            "/api/v1/students/me",
            json={"full_name": "Test Student", "phone": "9876543210", "batch_year": 2027},
            headers=auth_header(student_token),
        )
        assert updated.status_code == 200
        assert updated.json()["phone"] == "9876543210"
        assert updated.json()["batch_year"] == 2027

    def test_recruiter_cannot_access_student_me(self, client, recruiter_token):
        resp = client.get("/api/v1/students/me", headers=auth_header(recruiter_token))
        assert resp.status_code == 403

    def test_admin_can_list_students(self, client, student_token, admin_token):
        resp = client.get("/api/v1/students", headers=auth_header(admin_token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert any(s["full_name"] == "Test Student" for s in body["items"])

    def test_student_cannot_list_students(self, client, student_token):
        resp = client.get("/api/v1/students", headers=auth_header(student_token))
        assert resp.status_code == 403


class TestCompanies:
    def test_recruiter_can_create_company(self, client, recruiter_token):
        company = _create_company(client, recruiter_token)
        assert company["name"] == "Acme Corp"
        assert company["recruiter_id"] is not None

    def test_student_cannot_create_company(self, client, student_token):
        resp = client.post(
            "/api/v1/companies",
            json={"name": "Should Fail Inc"},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 403

    def test_any_authenticated_user_can_list_companies(self, client, recruiter_token, student_token):
        _create_company(client, recruiter_token)
        resp = client.get("/api/v1/companies", headers=auth_header(student_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_recruiter_cannot_update_another_recruiters_company(self, client, recruiter_token, db_session):
        company = _create_company(client, recruiter_token)

        # a second, unrelated recruiter
        second_token = client.post(
            "/api/v1/auth/register",
            json={
                "email": "recruiter2@example.com",
                "password": "StrongPass123",
                "role": "recruiter",
                "full_name": "Second Recruiter",
            },
        )
        assert second_token.status_code == 201
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "recruiter2@example.com", "password": "StrongPass123"},
        )
        second_recruiter_token = login.json()["access_token"]

        resp = client.put(
            f"/api/v1/companies/{company['id']}",
            json={"name": "Hijacked Name"},
            headers=auth_header(second_recruiter_token),
        )
        assert resp.status_code == 403


class TestJobs:
    def test_recruiter_can_create_and_view_job_with_required_skills(self, client, recruiter_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])

        assert job["title"] == "Python Developer"
        assert job["status"] == "open"
        skill_names = {s["skill"]["name"] for s in job["job_skills"]}
        assert skill_names == {"Python", "FastAPI"}

    def test_student_can_list_and_view_jobs_but_not_create(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        _create_job(client, recruiter_token, company["id"])

        listing = client.get("/api/v1/jobs", headers=auth_header(student_token))
        assert listing.status_code == 200
        assert listing.json()["total"] >= 1

        create_attempt = client.post(
            "/api/v1/jobs",
            json={"title": "Hacker Job", "description": "x" * 20, "company_id": company["id"]},
            headers=auth_header(student_token),
        )
        assert create_attempt.status_code == 403

    def test_job_filter_by_status(self, client, recruiter_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])

        close_resp = client.post(
            f"/api/v1/jobs/{job['id']}/close", headers=auth_header(recruiter_token)
        )
        assert close_resp.status_code == 200
        assert close_resp.json()["status"] == "closed"

        open_jobs = client.get("/api/v1/jobs?status=open", headers=auth_header(recruiter_token))
        assert all(j["status"] == "open" for j in open_jobs.json()["items"])

        closed_jobs = client.get("/api/v1/jobs?status=closed", headers=auth_header(recruiter_token))
        assert any(j["id"] == job["id"] for j in closed_jobs.json()["items"])


class TestApplications:
    def test_student_can_apply_and_view_own_applications(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])

        apply_resp = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        assert apply_resp.status_code == 201
        assert apply_resp.json()["status"] == "APPLIED"

        mine = client.get("/api/v1/applications/my", headers=auth_header(student_token))
        assert mine.status_code == 200
        assert len(mine.json()) == 1

    def test_duplicate_application_rejected(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])

        first = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        assert first.status_code == 201

        second = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        assert second.status_code == 409

    def test_cannot_apply_to_closed_job(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        client.post(f"/api/v1/jobs/{job['id']}/close", headers=auth_header(recruiter_token))

        resp = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        assert resp.status_code == 400

    def test_recruiter_can_update_status_of_own_job_application(
        self, client, recruiter_token, student_token
    ):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        apply_resp = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        application_id = apply_resp.json()["id"]

        update_resp = client.put(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "SHORTLISTED"},
            headers=auth_header(recruiter_token),
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "SHORTLISTED"

        # the student should now have a notification about it
        notifications = client.get(
            "/api/v1/notifications", headers=auth_header(student_token)
        )
        assert notifications.status_code == 200
        assert len(notifications.json()) >= 1

    def test_student_cannot_update_application_status(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        apply_resp = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        application_id = apply_resp.json()["id"]

        resp = client.put(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "SELECTED"},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 403

    def test_unrelated_recruiter_cannot_manage_application(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        apply_resp = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        application_id = apply_resp.json()["id"]

        client.post(
            "/api/v1/auth/register",
            json={
                "email": "otherrecruiter@example.com",
                "password": "StrongPass123",
                "role": "recruiter",
                "full_name": "Other Recruiter",
            },
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "otherrecruiter@example.com", "password": "StrongPass123"},
        )
        other_token = login.json()["access_token"]

        resp = client.put(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "REJECTED"},
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403


class TestAuditLogs:
    def test_admin_can_view_audit_logs_after_application(
        self, client, recruiter_token, student_token, admin_token
    ):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        client.post("/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token))

        resp = client.get("/api/v1/audit-logs", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_non_admin_cannot_view_audit_logs(self, client, recruiter_token):
        resp = client.get("/api/v1/audit-logs", headers=auth_header(recruiter_token))
        assert resp.status_code == 403
