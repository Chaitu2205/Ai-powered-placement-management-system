"""
Resume business logic: upload orchestration (validate -> store -> extract ->
persist -> mark as current), listing, and ownership-checked retrieval.
"""
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.enums import UserRole
from app.models.resume import Resume
from app.models.student import Student
from app.models.user import User
from app.services.resume_parser import extract_text
from app.utils.exceptions import NotFoundError, PermissionDeniedError
from app.utils.file_validation import generate_safe_storage_filename, validate_resume_upload

logger = logging.getLogger("app")
settings = get_settings()


def _storage_dir() -> Path:
    upload_dir = Path(settings.RESUME_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def upload_resume(
    db: Session, student: Student, *, original_filename: str, content_type: str, content: bytes
) -> Resume:
    file_type = validate_resume_upload(
        original_filename=original_filename,
        content_type=content_type,
        content=content,
        max_size_mb=settings.MAX_RESUME_SIZE_MB,
    )

    # Extraction failures are surfaced as a clean 400 (see ResumeParsingError)
    # rather than a 500 - a corrupted upload is a client-input problem, not a
    # server bug, and nothing is written to disk or the DB if this raises.
    extracted_text = extract_text(content, file_type)

    stored_filename = generate_safe_storage_filename(file_type)
    stored_path = _storage_dir() / stored_filename
    stored_path.write_bytes(content)

    resume = Resume(
        student_id=student.id,
        file_path=str(stored_path),
        file_type=file_type,
        original_filename=original_filename,
        extracted_text=extracted_text or None,
    )
    db.add(resume)
    db.flush()  # assign resume.id

    # The most recently uploaded resume becomes the student's "current" one,
    # used as the default when applying to jobs (see application_service).
    student.current_resume_id = resume.id

    db.commit()
    db.refresh(resume)
    return resume


def list_my_resumes(db: Session, student: Student) -> list[Resume]:
    return list(
        db.execute(
            select(Resume).where(Resume.student_id == student.id).order_by(Resume.uploaded_at.desc())
        )
        .scalars()
        .all()
    )


def get_resume(db: Session, current_user: User, resume_id: int) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise NotFoundError("Resume not found")

    if current_user.role == UserRole.ADMIN:
        return resume

    if current_user.role == UserRole.STUDENT:
        student = db.execute(
            select(Student).where(Student.user_id == current_user.id)
        ).scalar_one_or_none()
        if student is not None and resume.student_id == student.id:
            return resume

    raise PermissionDeniedError("You do not have permission to view this resume")
