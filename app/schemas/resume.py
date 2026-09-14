from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import ResumeFileType
from app.schemas.common import ORMBase


class ResumeRead(ORMBase):
    id: int
    student_id: int
    file_type: ResumeFileType
    original_filename: str
    uploaded_at: datetime


class ResumeDetailRead(ResumeRead):
    """ResumeRead plus the extracted text - used by GET /resumes/{id}."""
    extracted_text: Optional[str] = None


class ResumeAnalysisRead(ORMBase):
    id: int
    resume_id: int
    extracted_name: Optional[str]
    extracted_email: Optional[str]
    extracted_phone: Optional[str]
    education_json: Optional[list] = None
    projects_json: Optional[list] = None
    internships_json: Optional[list] = None
    certifications_json: Optional[list] = None
    experience_json: Optional[list] = None
    overall_score: Optional[int]
    detected_skills_json: Optional[list] = None
    strengths_json: Optional[list] = None
    weaknesses_json: Optional[list] = None
    missing_skills_json: Optional[list] = None
    suggestions_json: Optional[list] = None
    ats_keywords_json: Optional[list] = None
    summary_text: Optional[str]
    analyzed_at: datetime
