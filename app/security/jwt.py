"""
JWT access token creation and verification.

Tokens carry the user's id (as `sub`) and role, so `get_current_user` can
authenticate a request with a single DB lookup, and `require_role` can
authorize without touching the database at all.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import ValidationError

from app.config.settings import get_settings
from app.models.enums import UserRole
from app.schemas.user import TokenPayload
from app.utils.exceptions import UnauthorizedError

settings = get_settings()


def create_access_token(subject: str, role: UserRole, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    `subject` is the user's id (as a string, per JWT convention: `sub` must
    be a string claim).
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": subject, "role": role.value, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT access token.

    Raises `UnauthorizedError` (HTTP 401) if the token is missing, malformed,
    expired, or signed with the wrong key - callers never need to catch a
    raw jose/pydantic exception.
    """
    try:
        raw_payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**raw_payload)
    except (JWTError, ValidationError) as exc:
        raise UnauthorizedError("Invalid or expired authentication token") from exc
