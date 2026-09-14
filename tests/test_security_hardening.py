"""
Regression tests for Phase 12 security fixes.

Run with:
    pytest tests/test_security_hardening.py -v
"""
import json

from tests.conftest import auth_header


class TestValidationErrorDoesNotLeakInput:
    def test_registration_422_does_not_echo_submitted_password(self, client):
        secret_password = "TooShort1"[:5]  # deliberately fails the min_length=8 check
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "leaktest@example.com",
                "password": secret_password,
                "role": "student",
                "full_name": "Leak Test",
            },
        )
        assert resp.status_code == 422
        raw_body = json.dumps(resp.json())
        assert secret_password not in raw_body
        # "input" key must not appear anywhere in any error entry
        for error in resp.json()["errors"]:
            assert "input" not in error

    def test_login_422_does_not_echo_submitted_password(self, client):
        secret_password = "not-a-valid-email-but-has-a-password"
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": secret_password},
        )
        assert resp.status_code == 422
        raw_body = json.dumps(resp.json())
        assert secret_password not in raw_body

    def test_validation_error_still_returns_useful_fields(self, client):
        """The fix must not remove information a client actually needs to show a useful error."""
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "StrongPass123", "role": "student", "full_name": "X"},
        )
        assert resp.status_code == 422
        errors = resp.json()["errors"]
        assert len(errors) >= 1
        assert "loc" in errors[0]
        assert "msg" in errors[0]
        assert "type" in errors[0]


class TestProductionModeDisablesDocs:
    def test_docs_disabled_when_app_env_is_production(self, monkeypatch):
        """
        Directly exercises create_app()'s conditional rather than the
        already-instantiated test `app` (which was built once at import
        time with the test environment's APP_ENV and is cached/shared by
        every other test module - recreating it here, in isolation, with
        APP_ENV temporarily patched, is the only reliable way to test the
        production-mode branch without disturbing every other test).
        """
        import app.main as main_module

        monkeypatch.setattr(main_module.settings, "APP_ENV", "production")
        prod_app = main_module.create_app()

        assert prod_app.docs_url is None
        assert prod_app.redoc_url is None
        assert prod_app.openapi_url is None

    def test_docs_enabled_in_non_production_env(self, monkeypatch):
        import app.main as main_module

        monkeypatch.setattr(main_module.settings, "APP_ENV", "development")
        dev_app = main_module.create_app()

        assert dev_app.docs_url == "/docs"
        assert dev_app.redoc_url == "/redoc"
        assert dev_app.openapi_url == "/openapi.json"


class TestPlacementStatusUpdatesOnSelection:
    """
    Regression test for the Phase 11 analytics fix: Student.placement_status
    must actually change when an application is marked SELECTED, or the
    admin placement-percentage metric is permanently meaningless.
    """

    def test_marking_application_selected_updates_student_placement_status(
        self, client, recruiter_token, student_token, db_session
    ):
        from tests.test_core_placement import _create_company

        company = _create_company(client, recruiter_token)
        job = client.post(
            "/api/v1/jobs",
            json={"title": "Placement Test Job", "description": "x" * 20, "company_id": company["id"]},
            headers=auth_header(recruiter_token),
        ).json()
        application = client.post(
            "/api/v1/applications", json={"job_id": job["id"]}, headers=auth_header(student_token)
        ).json()

        me_before = client.get("/api/v1/students/me", headers=auth_header(student_token)).json()
        assert me_before["placement_status"] == "not_placed"

        client.put(
            f"/api/v1/applications/{application['id']}/status",
            json={"status": "SELECTED"},
            headers=auth_header(recruiter_token),
        )

        me_after = client.get("/api/v1/students/me", headers=auth_header(student_token)).json()
        assert me_after["placement_status"] == "selected"
