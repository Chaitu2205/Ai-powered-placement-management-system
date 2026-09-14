"""
Shared pytest fixtures.

Tests run against a SEPARATE MySQL database (default name
`placement_management_test`), never against the real `placement_management`
database. This matters because the schema uses a circular foreign key
(students.current_resume_id -> resumes.id via ALTER TABLE) which only
SQLite would have trouble with - running tests against real MySQL avoids
that entirely and matches production behavior exactly.

Set TEST_DATABASE_URL before running pytest to point at your own test DB,
e.g.:

    set TEST_DATABASE_URL=mysql+pymysql://placement_user:placement_pass@localhost:3306/placement_management_test

If it's not set, it defaults to the value below.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# These MUST be set before `app.config.settings.get_settings()` is first
# called (which happens on import of app.main / app.database.session), so
# we set them here, at the top of conftest, before any app import below.
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "mysql+pymysql://placement_user:placement_pass@localhost:3306/placement_management_test",
    ),
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-do-not-use-in-production")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("AI_API_KEY", "")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402,F401  (registers every model on Base.metadata)
from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security.hashing import hash_password  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, future=True)
TestingSessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Create every table in the TEST database once per test run, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """A TestClient whose `get_db` dependency is overridden to use the test DB session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clean_tables():
    """
    Truncate auth-relevant tables after every test so each test starts from
    a clean slate, without having to drop/recreate the schema each time.
    """
    yield
    with engine.begin() as conn:
        # Delete order matters (children before parents) because of FKs.
        for table_name in (
            "audit_logs",
            "notifications",
            "applications",
            "job_skills",
            "jobs",
            "companies",
            "placement_drives",
            "student_skills",
            "recruiters",
            "students",
            "users",
            "skills",
            "departments",
        ):
            conn.execute(Base.metadata.tables[table_name].delete())


def _register_and_login(client, *, email: str, password: str, role: str, full_name: str, **extra) -> str:
    """Register a student/recruiter through the real API, log in, return a bearer token."""
    register_body = {"email": email, "password": password, "role": role, "full_name": full_name, **extra}
    resp = client.post("/api/v1/auth/register", json=register_body)
    assert resp.status_code == 201, resp.text

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200, login_resp.text
    return login_resp.json()["access_token"]


@pytest.fixture()
def student_token(client):
    return _register_and_login(
        client, email="student@example.com", password="StrongPass123", role="student", full_name="Test Student"
    )


@pytest.fixture()
def recruiter_token(client):
    return _register_and_login(
        client,
        email="recruiter@example.com",
        password="StrongPass123",
        role="recruiter",
        full_name="Test Recruiter",
        designation="HR Manager",
    )


@pytest.fixture()
def admin_token(client, db_session):
    """
    Admin accounts cannot be created through public registration, so this
    fixture inserts one directly into the test DB (bypassing the API, which
    is the whole point of the restriction) and logs in through the real
    /auth/login endpoint.
    """
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("StrongPass123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "StrongPass123"}
    )
    assert login_resp.status_code == 200, login_resp.text
    return login_resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
