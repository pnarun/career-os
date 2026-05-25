"""Pydantic models for Resume AI / ATS intelligence API."""

from typing import Any

from pydantic import BaseModel, Field


class AtsScoreResponse(BaseModel):
    resume_id: str
    ats_score: int
    keyword_score: int
    format_score: int
    skills_score: int
    experience_score: int
    factors: dict[str, int] = Field(default_factory=dict)
    section_analysis: dict[str, Any] = Field(default_factory=dict)


class ResumeFeedbackResponse(BaseModel):
    resume_id: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    high_impact_changes: list[str] = Field(default_factory=list)
    ats_summary: dict[str, int] = Field(default_factory=dict)


class KeywordOptimizationResponse(BaseModel):
    resume_id: str
    coverage_percent: int
    missing_keywords: list[dict[str, str]] = Field(default_factory=list)
    underrepresented_keywords: list[dict[str, str]] = Field(default_factory=list)
    present_keywords: list[str] = Field(default_factory=list)
    weak_terminology: list[dict[str, str]] = Field(default_factory=list)


class SkillGapResponse(BaseModel):
    resume_id: str
    top_missing_skills: list[dict[str, Any]] = Field(default_factory=list)
    strongest_area: str = ""
    growth_recommendation: str = ""
    learning_recommendations: list[dict[str, str]] = Field(default_factory=list)
    skill_radar: list[dict[str, Any]] = Field(default_factory=list)


class JdAlignmentRequest(BaseModel):
    resume_id: str = ""
    job_description: str = Field(..., min_length=20)
    job_title: str = ""
    job_location: str = ""
    job_remote: bool = False


class JdAlignmentResponse(BaseModel):
    resume_id: str
    alignment_score: int
    matched_skills: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    suggested_additions: list[str] = Field(default_factory=list)
    weak_sections: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    reorder_suggestions: list[str] = Field(default_factory=list)
    keyword_coverage: int = 0
    match_breakdown: dict[str, Any] = Field(default_factory=dict)


class TailorResumeRequest(BaseModel):
    resume_id: str = ""
    job_id: str = ""
    job_description: str = ""
    job_title: str = ""
    job_location: str = ""
    job_remote: bool = False


class TailorResumeResponse(BaseModel):
    resume_id: str
    job_title: str = ""
    alignment_score: int
    ats_score_before: int
    ats_score_tailored: int
    projected_ats_score: int
    improvement_potential_percent: int = 0
    improvement_summary: str = ""
    genuine_missing_skills: list[str] = Field(default_factory=list)
    optimization_plan: list[dict[str, str]] = Field(default_factory=list)
    alignment: dict[str, Any] = Field(default_factory=dict)
    feedback: dict[str, Any] = Field(default_factory=dict)
    keyword_analysis: dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = ""


class ResumeVariantItem(BaseModel):
    variant_id: str
    label: str
    focus_skills: list[str] = Field(default_factory=list)
    match_score: int
    summary_hint: str = ""
    recommended_sections_order: list[str] = Field(default_factory=list)
    emphasis_recommendations: list[str] = Field(default_factory=list)


class ResumeVariantsResponse(BaseModel):
    resume_id: str
    variants: list[ResumeVariantItem] = Field(default_factory=list)
    recommended_variant: str = ""
    master_skill_count: int = 0


class ResumeExportRequest(BaseModel):
    resume_id: str = ""
    format: str = "txt"
    variant_id: str | None = None


class ResumeExportResponse(BaseModel):
    resume_id: str
    format: str
    filename: str
    content_type: str
    content: str | None = None
    data_base64: str | None = None
    plain_preview: str = ""


class ResumeAiOverviewResponse(BaseModel):
    resume_id: str
    resume_filename: str
    ats: AtsScoreResponse
    feedback: ResumeFeedbackResponse
    keywords: KeywordOptimizationResponse
    skill_gaps: SkillGapResponse
    variants: ResumeVariantsResponse
