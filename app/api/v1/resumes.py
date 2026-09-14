from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.ai.resume_analyzer import ResumeAnalyzerProvider, get_resume_analyzer_provider
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.resume import ResumeAnalysisRead, ResumeDetailRead, ResumeRead
from app.security.dependencies import get_current_user, require_role
from app.services import resume_analysis_service, resume_service
from app.services.student_service import get_student_by_user_id

router = APIRouter()


@router.post("/upload", response_model=ResumeRead, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> ResumeRead:
    """
    Upload a PDF or DOCX resume. The most recently uploaded resume becomes
    the student's current resume. Validation (type/size/corruption) happens
    before anything is written to disk or the database.
    """
    student = get_student_by_user_id(db, current_user.id)
    content = await file.read()
    return resume_service.upload_resume(
        db,
        student,
        original_filename=file.filename or "resume",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )


@router.get("/my", response_model=list[ResumeRead])
def list_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> list:
    student = get_student_by_user_id(db, current_user.id)
    return resume_service.list_my_resumes(db, student)


@router.get("/{resume_id}", response_model=ResumeDetailRead)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeDetailRead:
    """Returns resume metadata plus its extracted text. Owner student or admin only."""
    return resume_service.get_resume(db, current_user, resume_id)


@router.get("/{resume_id}/download")
def download_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Streams the original uploaded file. Owner student or admin only - never served as a static file."""
    resume = resume_service.get_resume(db, current_user, resume_id)
    media_type = "application/pdf" if resume.file_type.value == "pdf" else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(
        path=resume.file_path,
        media_type=media_type,
        filename=resume.original_filename,
    )


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisRead, status_code=201)
def analyze_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: ResumeAnalyzerProvider = Depends(get_resume_analyzer_provider),
) -> ResumeAnalysisRead:
    """
    Runs AI analysis on the resume's extracted text and stores a new
    analysis record (history is preserved - re-analyzing doesn't overwrite
    a previous result). Owner student or admin only; recruiters are not
    granted access to this endpoint.
    """
    return resume_analysis_service.analyze_resume(db, current_user, resume_id, provider)


@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisRead)
def get_resume_analysis(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeAnalysisRead:
    """Returns the most recent analysis for this resume. Owner student or admin only."""
    return resume_analysis_service.get_latest_analysis(db, current_user, resume_id)
