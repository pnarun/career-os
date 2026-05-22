from pydantic import BaseModel, Field


class MatchJobRequest(BaseModel):
    resume_id: str = ""
    job_description: str = Field(..., min_length=10)


class MatchJobResponse(BaseModel):
    match_percentage: int
    matched_skills: list[str]
    missing_skills: list[str]
    job_skills: list[str]
    recommendation: str
    resume_id: str
