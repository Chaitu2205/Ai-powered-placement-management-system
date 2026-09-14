"""
Pure text-extraction functions for resume files.

Deliberately has no knowledge of HTTP, the database, or students - it just
takes raw file bytes and returns extracted text (or raises on a genuinely
corrupted file). This keeps it independently testable and reusable by the
Phase 7 AI analyzer without any changes.
"""
import io
import logging

import fitz  # PyMuPDF
from docx import Document

from app.models.enums import ResumeFileType
from app.utils.exceptions import AppException
from fastapi import status as http_status

logger = logging.getLogger("app")


class ResumeParsingError(AppException):
    def __init__(self, message: str = "Could not read this file - it may be corrupted"):
        super().__init__(message, status_code=http_status.HTTP_400_BAD_REQUEST)


def extract_text_from_pdf(content: bytes) -> str:
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            pages = [page.get_text() for page in doc]
        return "\n".join(pages).strip()
    except Exception as exc:  # PyMuPDF raises its own RuntimeError/fitz errors on corrupt files
        logger.warning("PDF text extraction failed: %s", exc)
        raise ResumeParsingError() from exc


def extract_text_from_docx(content: bytes) -> str:
    try:
        document = Document(io.BytesIO(content))
        paragraphs = [p.text for p in document.paragraphs]
        # Tables are common in resumes (skills grids, education tables) - include them.
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        paragraphs.append(cell.text)
        return "\n".join(p for p in paragraphs if p.strip()).strip()
    except Exception as exc:  # python-docx raises various errors on a malformed .docx
        logger.warning("DOCX text extraction failed: %s", exc)
        raise ResumeParsingError() from exc


def extract_text(content: bytes, file_type: ResumeFileType) -> str:
    if file_type == ResumeFileType.PDF:
        return extract_text_from_pdf(content)
    return extract_text_from_docx(content)
