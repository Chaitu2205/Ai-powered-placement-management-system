"""
/api/v1/auth routes.

Kept deliberately thin: each route parses/validates the request (via the
Pydantic schema in the signature), delegates to `auth_service`, and shapes
the response. No business logic lives here.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.user import TokenResponse, UserLogin, UserRead
from app.security.dependencies import get_current_user
from app.security.jwt import create_access_token
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student or recruiter account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """
    Public registration. `role` only accepts "student" or "recruiter" at the
    schema level - admin accounts cannot be created through this endpoint.
    """
    return auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive a JWT access token",
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    token = create_access_token(subject=str(user.id), role=user.role)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
