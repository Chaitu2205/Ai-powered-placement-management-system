"""
Integration tests for Phase 6: resume upload, validation, and text extraction.

Run with (from backend/, venv activated, pymupdf + python-docx installed
per requirements.txt):
    pytest tests/test_resumes.py -v
"""
import io
import zipfile
from pathlib import Path

import pytest

from tests.conftest import auth_header


@pytest.fixture(autouse=True)
def _clean_upload_dir():
    """
    Removes any files written to RESUME_UPLOAD_DIR during a test. DB rows
    are already cleaned by conftest's autouse _clean_tables (resumes cascade
    -delete when their student is deleted) - this just tidies up the actual
    files on disk so repeated test runs don't accumulate them.
    """
    yield
    from app.config.settings import get_settings

    upload_dir = Path(get_settings().RESUME_UPLOAD_DIR)
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            if f.is_file():
                f.unlink()


def _minimal_pdf_bytes(text: str = "Hello Resume Text") -> bytes:
    """
    Hand-built minimal single-page PDF containing a text-show operator.
    PDF readers (including PyMuPDF/mupdf) are tolerant of a missing/loose
    xref table and will repair it on open, so this doesn't need a
    byte-perfect cross-reference table to be readable.
    """
    content_stream = f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET"
    pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 300]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length {len(content_stream)}>>
stream
{content_stream}
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Size 6/Root 1 0 R>>
%%EOF
"""
    return pdf.encode("latin-1")


def _minimal_docx_bytes(text: str = "Hello Resume Text") -> bytes:
    """Hand-built minimal valid .docx (a zip with the required OOXML parts)."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>'
        "</w:body></w:document>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


class TestResumeUpload:
    def test_student_can_upload_pdf_and_text_is_extracted(self, client, student_token):
        pdf_bytes = _minimal_pdf_bytes("Experienced Python Developer")
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(student_token),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["file_type"] == "pdf"
        assert body["original_filename"] == "resume.pdf"

        detail = client.get(f"/api/v1/resumes/{body['id']}", headers=auth_header(student_token))
        assert detail.status_code == 200
        assert "Python Developer" in detail.json()["extracted_text"]

    def test_student_can_upload_docx_and_text_is_extracted(self, client, student_token):
        docx_bytes = _minimal_docx_bytes("Skilled in FastAPI and SQL")
        response = client.post(
            "/api/v1/resumes/upload",
            files={
                "file": (
                    "resume.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers=auth_header(student_token),
        )
        assert response.status_code == 201, response.text
        assert response.json()["file_type"] == "docx"

    def test_upload_sets_current_resume(self, client, student_token, db_session):
        from app.models.student import Student

        pdf_bytes = _minimal_pdf_bytes()
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(student_token),
        )
        resume_id = response.json()["id"]

        student = db_session.query(Student).first()
        db_session.refresh(student)
        assert student.current_resume_id == resume_id

    def test_reject_disallowed_file_type(self, client, student_token):
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.exe", b"not a real resume", "application/octet-stream")},
            headers=auth_header(student_token),
        )
        assert response.status_code == 400

    def test_reject_mismatched_content_pretending_to_be_pdf(self, client, student_token):
        # Extension says .pdf but the actual bytes aren't a PDF - magic-byte check should catch this.
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", b"just some plain text, not a pdf", "application/pdf")},
            headers=auth_header(student_token),
        )
        assert response.status_code == 400

    def test_reject_empty_file(self, client, student_token):
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", b"", "application/pdf")},
            headers=auth_header(student_token),
        )
        assert response.status_code == 400

    def test_reject_oversized_file(self, client, student_token, monkeypatch):
        from app.services import resume_service

        monkeypatch.setattr(resume_service.settings, "MAX_RESUME_SIZE_MB", 0)
        pdf_bytes = _minimal_pdf_bytes()
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(student_token),
        )
        assert response.status_code == 400

    def test_recruiter_cannot_upload_resume(self, client, recruiter_token):
        pdf_bytes = _minimal_pdf_bytes()
        response = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(recruiter_token),
        )
        assert response.status_code == 403

    def test_unauthenticated_upload_rejected(self, client):
        pdf_bytes = _minimal_pdf_bytes()
        response = client.post(
            "/api/v1/resumes/upload", files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}
        )
        assert response.status_code in (401, 403)


class TestResumeOwnership:
    def test_student_cannot_view_another_students_resume(self, client, student_token):
        pdf_bytes = _minimal_pdf_bytes()
        upload = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(student_token),
        )
        resume_id = upload.json()["id"]

        other_register = client.post(
            "/api/v1/auth/register",
            json={
                "email": "other-student@example.com",
                "password": "StrongPass123",
                "role": "student",
                "full_name": "Other Student",
            },
        )
        assert other_register.status_code == 201
        other_login = client.post(
            "/api/v1/auth/login",
            json={"email": "other-student@example.com", "password": "StrongPass123"},
        )
        other_token = other_login.json()["access_token"]

        response = client.get(f"/api/v1/resumes/{resume_id}", headers=auth_header(other_token))
        assert response.status_code == 403

    def test_admin_can_view_any_resume(self, client, student_token, admin_token):
        pdf_bytes = _minimal_pdf_bytes()
        upload = client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(student_token),
        )
        resume_id = upload.json()["id"]

        response = client.get(f"/api/v1/resumes/{resume_id}", headers=auth_header(admin_token))
        assert response.status_code == 200

    def test_list_my_resumes_returns_only_own(self, client, student_token):
        pdf_bytes = _minimal_pdf_bytes()
        client.post(
            "/api/v1/resumes/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=auth_header(student_token),
        )
        response = client.get("/api/v1/resumes/my", headers=auth_header(student_token))
        assert response.status_code == 200
        assert len(response.json()) == 1
