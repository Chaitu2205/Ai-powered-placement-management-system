"""
Pure unit tests for the security layer. These don't hit the database or an
HTTP client - they call the security functions/dependencies directly, so
they're fast and isolate failures precisely.

Run with:
    pytest tests/test_security.py -v
"""
from datetime import timedelta

import pytest

from app.models.enums import UserRole
from app.security.dependencies import require_role
from app.security.hashing import hash_password, verify_password
from app.security.jwt import create_access_token, decode_access_token
from app.utils.exceptions import PermissionDeniedError, UnauthorizedError


class TestHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MySecretPass1")
        assert hashed != "MySecretPass1"
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_correct_password(self):
        hashed = hash_password("MySecretPass1")
        assert verify_password("MySecretPass1", hashed) is True

    def test_verify_incorrect_password(self):
        hashed = hash_password("MySecretPass1")
        assert verify_password("WrongPassword", hashed) is False

    def test_same_password_hashes_differently_each_time(self):
        # bcrypt uses a random salt per call - this guards against a
        # regression where salting is accidentally removed.
        assert hash_password("SamePassword1") != hash_password("SamePassword1")


class TestJWT:
    def test_create_and_decode_round_trip(self):
        token = create_access_token(subject="42", role=UserRole.STUDENT)
        payload = decode_access_token(token)
        assert payload.sub == "42"
        assert payload.role == UserRole.STUDENT

    def test_expired_token_is_rejected(self):
        token = create_access_token(
            subject="1", role=UserRole.ADMIN, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(UnauthorizedError):
            decode_access_token(token)

    def test_tampered_token_is_rejected(self):
        token = create_access_token(subject="1", role=UserRole.STUDENT)
        tampered = token[:-4] + "abcd"  # corrupt the signature
        with pytest.raises(UnauthorizedError):
            decode_access_token(tampered)

    def test_garbage_token_is_rejected(self):
        with pytest.raises(UnauthorizedError):
            decode_access_token("this-is-not-a-jwt")


class _FakeUser:
    """Minimal stand-in for the User ORM model - just needs a `.role`."""
    def __init__(self, role: UserRole):
        self.role = role


class TestRequireRole:
    def test_allows_matching_role(self):
        dependency = require_role(UserRole.ADMIN)
        # require_role's inner function takes current_user via Depends, but
        # calling it directly with a positional arg works the same way.
        result = dependency(current_user=_FakeUser(UserRole.ADMIN))
        assert result.role == UserRole.ADMIN

    def test_allows_one_of_multiple_roles(self):
        dependency = require_role(UserRole.ADMIN, UserRole.RECRUITER)
        result = dependency(current_user=_FakeUser(UserRole.RECRUITER))
        assert result.role == UserRole.RECRUITER

    def test_rejects_non_matching_role(self):
        dependency = require_role(UserRole.ADMIN)
        with pytest.raises(PermissionDeniedError):
            dependency(current_user=_FakeUser(UserRole.STUDENT))
