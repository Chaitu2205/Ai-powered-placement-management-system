from pydantic import BaseModel, Field


class JobMatchRead(BaseModel):
    job_id: int
    job_title: str
    match_score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    recommendation: str


class RecommendedJobRead(JobMatchRead):
    company_name: str
