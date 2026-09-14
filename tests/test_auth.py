"""
Integration tests for Phase 3 auth endpoints.

Run with (from backend/, venv activated):
    pytest tests/test_auth.py -v
"""


def _register_student(client, email="student1@example.com", password="StrongPass123"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "student",
            "full_name": "Asha Rao",
            "phone": "9999999999",
            "batch_year": 2026,
        },
    )


def _register_recruiter(client, email="recruiter1@example.com", password="StrongPass123"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "recruiter",
            "full_name": "Priya Nair",
            "designation": "Talent Acquisition Lead",
        },
    )


class TestRegistration:
    def test_register_student_success(self, client):
        response = _register_student(client)
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "student1@example.com"
        assert body["role"] == "student"
        assert body["is_active"] is True
        # password must never be echoed back
        assert "password" not in body
        assert "password_hash" not in body

    def test_register_recruiter_success(self, client):
        response = _register_recruiter(client)
        assert response.status_code == 201
        body = response.json()
        assert body["role"] == "recruiter"

    def test_register_duplicate_email_rejected(self, client):
        first = _register_student(client, email="dupe@example.com")
        assert first.status_code == 201

        second = _register_student(client, email="dupe@example.com")
        assert second.status_code == 409
        assert "already exists" in second.json()["detail"].lower()

    def test_register_admin_role_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "wannabe-admin@example.com",
                "password": "StrongPass123",
                "role": "admin",
                "full_name": "Someone",
            },
        )
        # Pydantic validation rejects "admin" before it reaches the DB.
        assert response.status_code == 422

    def test_register_weak_password_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpw@example.com",
                "password": "short",
                "role": "student",
                "full_name": "Weak Pw",
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "StrongPass123",
                "role": "student",
                "full_name": "Bad Email",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        _register_student(client, email="login@example.com", password="StrongPass123")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "StrongPass123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20

    def test_login_wrong_password(self, client):
        _register_student(client, email="wrongpw@example.com", password="StrongPass123")

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "TotallyWrongPass1"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "StrongPass123"},
        )
        assert response.status_code == 401


class TestMe:
    def test_me_with_valid_token(self, client):
        _register_student(client, email="me@example.com", password="StrongPass123")
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "StrongPass123"},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    def test_me_without_token(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)  # HTTPBearer raises 403 if header is entirely missing

    def test_me_with_garbage_token(self, client):
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401
