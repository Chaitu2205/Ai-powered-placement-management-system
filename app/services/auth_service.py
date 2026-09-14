"""
Authentication service.

Contains all auth business logic so `app/api/v1/auth.py` stays a thin
request/response layer. Nothing here talks HTTP - it raises `AppException`
subclasses, which the global exception handlers (app/utils/exceptions.py)
turn into the right HTTP responses.
"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.recruiter import Recruiter
from app.models.student import Student
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.security.hashing import hash_password, verify_password
from app.utils.exceptions import ConflictError, UnauthorizedError


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def register_user(db: Session, payload: RegisterRequest) -> User:
    """
    Atomically create a `User` row plus its matching `Student` or
    `Recruiter` profile row. Either both are created or neither is - if the
    profile insert fails, the whole transaction is rolled back so we never
    end up with a `User` that has no profile.
    """
    if get_user_by_email(db, payload.email) is not None:
        raise ConflictError("An account with this email already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)

    try:
        # Flush (not commit) so `user.id` is assigned without ending the
        # transaction - the profile row below is inserted in the SAME
        # transaction, giving us atomic User+Profile creation.
        db.flush()

        if payload.role == UserRole.STUDENT:
            profile = Student(
                user_id=user.id,
                full_name=payload.full_name,
                phone=payload.phone,
                department_id=payload.department_id,
                batch_year=payload.batch_year,
                cgpa=payload.cgpa,
            )
        else:  # UserRole.RECRUITER (the only other value RegisterRequest allows)
            profile = Recruiter(
                user_id=user.id,
                full_name=payload.full_name,
                designation=payload.designation,
                phone=payload.phone,
            )

        db.add(profile)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Most likely a race: two concurrent requests registered the same
        # email between our check above and the insert.
        raise ConflictError("An account with this email already exists")

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials and return the user, or raise 401."""
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated")
    return user
