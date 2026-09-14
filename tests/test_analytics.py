"""
Integration tests for Phase 11: analytics endpoints.

Run with:
    pytest tests/test_analytics.py -v
"""
from tests.conftest import auth_header
from tests.test_core_placement import _create_company


def _create_job(client, recruiter_token, company_id, title="Analytics Test Job"):
    resp = client.post(
        "/api/v1/jobs",
        json={
            "title": title,
            "description": "A role used purely for analytics testing.",
            "company_id": company_id,
        },
        headers=auth_header(recruiter_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestStudentAnalytics:
    def test_student_sees_own_analytics(self, client, student_token, recruiter_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        client.post("/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token))

        resp = client.get("/api/v1/analytics/student", headers=auth_header(student_token))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_applications"] == 1
        assert any(s["status"] == "APPLIED" and s["count"] == 1 for s in body["applications_by_status"])
        assert body["open_jobs_count"] >= 1
        assert isinstance(body["recommended_jobs"], list)
        assert body["total_interview_sessions"] == 0
        assert body["resume_score"] is None  # no resume uploaded/analyzed in this test

    def test_recruiter_and_admin_cannot_access_student_analytics(self, client, recruiter_token, admin_token):
        assert client.get("/api/v1/analytics/student", headers=auth_header(recruiter_token)).status_code == 403
        assert client.get("/api/v1/analytics/student", headers=auth_header(admin_token)).status_code == 403

    def test_unauthenticated_request_rejected(self, client):
        resp = client.get("/api/v1/analytics/student")
        assert resp.status_code in (401, 403)


class TestRecruiterAnalytics:
    def test_recruiter_sees_only_own_jobs(self, client, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        client.post("/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token))

        # a second, unrelated recruiter with their own job - must not appear in the first recruiter's stats
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "recruiter-analytics2@example.com",
                "password": "StrongPass123",
                "role": "recruiter",
                "full_name": "Second Recruiter",
            },
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "recruiter-analytics2@example.com", "password": "StrongPass123"},
        )
        second_token = login.json()["access_token"]
        second_company = _create_company(client, second_token, name="Other Co")
        _create_job(client, second_token, second_company["id"], title="Unrelated Job")

        resp = client.get("/api/v1/analytics/recruiter", headers=auth_header(recruiter_token))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_jobs_posted"] == 1
        assert body["active_jobs"] == 1
        assert body["total_applications_received"] == 1
        assert len(body["applicants_per_job"]) == 1
        assert body["applicants_per_job"][0]["job_title"] == "Analytics Test Job"
        assert body["applicants_per_job"][0]["applicant_count"] == 1

    def test_closed_jobs_counted_correctly(self, client, recruiter_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        client.post(f"/api/v1/jobs/{job['id']}/close", headers=auth_header(recruiter_token))

        resp = client.get("/api/v1/analytics/recruiter", headers=auth_header(recruiter_token))
        body = resp.json()
        assert body["active_jobs"] == 0
        assert body["closed_jobs"] == 1

    def test_student_and_admin_cannot_access_recruiter_analytics(self, client, student_token, admin_token):
        assert client.get("/api/v1/analytics/recruiter", headers=auth_header(student_token)).status_code == 403
        assert client.get("/api/v1/analytics/recruiter", headers=auth_header(admin_token)).status_code == 403


class TestAdminAnalytics:
    def test_admin_sees_system_wide_totals(self, client, admin_token, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        client.post("/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token))

        resp = client.get("/api/v1/analytics/admin", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_students"] >= 1
        assert body["total_recruiters"] >= 1
        assert body["total_companies"] >= 1
        assert body["total_jobs"] >= 1
        assert body["total_applications"] >= 1
        assert 0 <= body["placement_percentage"] <= 100
        assert isinstance(body["monthly_application_trend"], list)

    def test_placement_percentage_reflects_selected_students(self, client, admin_token, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job = _create_job(client, recruiter_token, company["id"])
        apply_resp = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        )
        application_id = apply_resp.json()["id"]

        before = client.get("/api/v1/analytics/admin", headers=auth_header(admin_token)).json()

        client.put(
            f"/api/v1/applications/{application_id}/status",
            json={"status": "SELECTED"},
            headers=auth_header(recruiter_token),
        )

        after = client.get("/api/v1/analytics/admin", headers=auth_header(admin_token)).json()
        assert after["placement_percentage"] > before["placement_percentage"]
        assert any(
            s["status"] == "selected" and s["count"] >= 1 for s in after["students_by_placement_status"]
        )

    def test_selected_status_not_downgraded_by_later_shortlist(self, client, admin_token, recruiter_token, student_token):
        company = _create_company(client, recruiter_token)
        job1 = _create_job(client, recruiter_token, company["id"], title="Job A")
        job2 = _create_job(client, recruiter_token, company["id"], title="Job B")

        app1 = client.post(
            "/api/v1/applications", json={"job_id": job1["id"]}, headers=auth_header(student_token)
        ).json()
        app2 = client.post(
            "/api/v1/applications", json={"job_id": job2["id"]}, headers=auth_header(student_token)
        ).json()

        client.put(
            f"/api/v1/applications/{app1['id']}/status",
            json={"status": "SELECTED"},
            headers=auth_header(recruiter_token),
        )
        client.put(
            f"/api/v1/applications/{app2['id']}/status",
            json={"status": "SHORTLISTED"},
            headers=auth_header(recruiter_token),
        )

        resp = client.get("/api/v1/analytics/admin", headers=auth_header(admin_token))
        statuses = {s["status"]: s["count"] for s in resp.json()["students_by_placement_status"]}
        assert statuses.get("selected", 0) >= 1
        # the student must still show as "selected", not have been downgraded to "shortlisted"

    def test_student_and_recruiter_cannot_access_admin_analytics(self, client, student_token, recruiter_token):
        assert client.get("/api/v1/analytics/admin", headers=auth_header(student_token)).status_code == 403
        assert client.get("/api/v1/analytics/admin", headers=auth_header(recruiter_token)).status_code == 403
