"""
Validation and safe-storage helpers for uploaded resume files.

Nothing here trusts the client: the original filename is only ever used for
display, never for building a filesystem path, and every check happens
server-side regardless of what Content-Type the browser claims.
"""
import uuid
from pathlib import Path

from app.models.enums import ResumeFileType
from app.utils.exceptions import AppException
from fastapi import status as http_status

ALLOWED_EXTENSIONS = {".pdf": ResumeFileType.PDF, ".docx": ResumeFileType.DOCX}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Some browsers/tools send this generic type for .docx - still validated
    # against the actual file extension below, so this alone can't smuggle
    # anything through.
    "application/octet-stream",
}

# Magic bytes for the two supported formats - checked against the actual
# uploaded content, not just the filename or declared content-type.
_PDF_MAGIC = b"%PDF-"
_DOCX_MAGIC = b"PK\x03\x04"  # DOCX is a ZIP archive


class UnsupportedFileTypeError(AppException):
    def __init__(self, message: str = "Only PDF and DOCX resumes are supported"):
        super().__init__(message, status_code=http_status.HTTP_400_BAD_REQUEST)


class FileTooLargeError(AppException):
    def __init__(self, max_mb: int):
        super().__init__(
            f"File is too large. Maximum allowed size is {max_mb} MB.",
            status_code=http_status.HTTP_400_BAD_REQUEST,
        )


class EmptyFileError(AppException):
    def __init__(self):
        super().__init__("The uploaded file is empty", status_code=http_status.HTTP_400_BAD_REQUEST)


def validate_resume_upload(
    *, original_filename: str, content_type: str, content: bytes, max_size_mb: int
) -> ResumeFileType:
    """
    Validates a resume upload and returns its detected ResumeFileType.
    Raises an AppException subclass (400) on any validation failure.
    """
    if not content:
        raise EmptyFileError()

    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(max_size_mb)

    extension = Path(original_filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError()

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported content type '{content_type}'. Upload a PDF or DOCX file."
        )

    file_type = ALLOWED_EXTENSIONS[extension]

    # Verify the actual bytes match the claimed format (magic-byte check),
    # so a renamed .exe with a .pdf extension is still rejected.
    if file_type == ResumeFileType.PDF and not content.startswith(_PDF_MAGIC):
        raise UnsupportedFileTypeError("File does not look like a valid PDF")
    if file_type == ResumeFileType.DOCX and not content.startswith(_DOCX_MAGIC):
        raise UnsupportedFileTypeError("File does not look like a valid DOCX")

    return file_type


def generate_safe_storage_filename(file_type: ResumeFileType) -> str:
    """
    Never use the user-supplied filename to build a path (path traversal,
    collisions, weird characters). Generate a fresh UUID-based name instead;
    the original filename is kept only as display metadata in the DB.
    """
    extension = "pdf" if file_type == ResumeFileType.PDF else "docx"
    return f"{uuid.uuid4().hex}.{extension}"
