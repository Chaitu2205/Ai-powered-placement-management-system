"""
FastAPI dependencies for authentication and role-based authorization.

Usage in a route:

    @router.get("/students/me")
    def read_own_profile(current_user: User = Depends(get_current_user)):
        ...

    @router.get("/admin/students")
    def list_students(current_user: User = Depends(require_role(UserRole.ADMIN))):
        ...
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.security.jwt import decode_access_token
from app.utils.exceptions import PermissionDeniedError, UnauthorizedError

# HTTPBearer (rather than OAuth2PasswordBearer) matches this API's JSON-body
# login (POST /auth/login with {"email": ..., "password": ...}) instead of
# the OAuth2 form-encoded password flow. In Swagger UI this renders as a
# simple "paste your bearer token" Authorize dialog.
_bearer_scheme = HTTPBearer(auto_error=True, description="Paste the access token returned by /auth/login")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the JWT in the Authorization header to an active User row."""
    payload = decode_access_token(credentials.credentials)

    try:
        user_id = int(payload.sub)
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid authentication token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User account not found or inactive")

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory: returns a dependency that only lets through users
    whose role is in `allowed_roles`. Example:

        Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER))
    """
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError(
                f"This action requires one of the following roles: "
                f"{', '.join(role.value for role in allowed_roles)}"
            )
        return current_user

    return _dependency
