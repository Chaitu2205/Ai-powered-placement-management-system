"""
The structured contract every resume-analysis AI provider must return.

This is the validation boundary between "whatever the LLM said" and "what
we're willing to store in the database or send to the frontend." Any
provider - real or mock - must produce data that validates against this
model before resume_analysis_service will persist it.
"""
from typing import Optional

from pydantic import BaseModel, Field


class AIResumeAnalysisResult(BaseModel):
    extracted_name: Optional[str] = None
    extracted_email: Optional[str] = None
    extracted_phone: Optional[str] = None

    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    internships: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)

    detected_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    ats_keywords: list[str] = Field(default_factory=list)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    overall_score: int = Field(ge=0, le=100)
    summary: str = ""
