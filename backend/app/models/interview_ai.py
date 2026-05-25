"""Pydantic models for Interview AI / career preparation API."""

from typing import Any

from pydantic import BaseModel, Field


class InterviewJobRequest(BaseModel):
    resume_id: str = ""
    job_id: str = ""
    job_description: str = ""
    job_title: str = ""
    company: str = ""
    job_location: str = ""


class ReadinessResponse(BaseModel):
    resume_id: str | None = None
    job_id: str = ""
    readiness_score: int
    technical_readiness: int
    behavioral_readiness: int
    system_design_readiness: int
    focus_label: str = ""
    weak_areas: list[str] = Field(default_factory=list)
    topic_confidence: list[dict[str, Any]] = Field(default_factory=list)
    question_count: int = 0


class InterviewQuestionItem(BaseModel):
    question: str
    topic: str = ""
    category: str = ""
    tip: str = ""
    source: str = ""


class QuestionsResponse(BaseModel):
    job_id: str = ""
    focus_label: str = ""
    question_source: str = "static"
    technical_questions: list[InterviewQuestionItem] = Field(default_factory=list)
    behavioral_questions: list[InterviewQuestionItem] = Field(default_factory=list)
    system_design_prompts: list[InterviewQuestionItem] = Field(default_factory=list)
    project_questions: list[InterviewQuestionItem] = Field(default_factory=list)
    resume_based_questions: list[InterviewQuestionItem] = Field(default_factory=list)
    total_count: int = 0


class TopicsResponse(BaseModel):
    job_id: str = ""
    technologies: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    architecture_concepts: list[str] = Field(default_factory=list)
    cloud_tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    role_emphasis: str = ""
    primary_stack: list[str] = Field(default_factory=list)


class TechnicalFocusResponse(BaseModel):
    focus_type: str
    focus_label: str
    prioritized_areas: list[str] = Field(default_factory=list)
    tech_priorities: list[dict[str, str]] = Field(default_factory=list)


class CodingTopicsResponse(BaseModel):
    role_emphasis: str = ""
    dsa_topics: list[str] = Field(default_factory=list)
    system_design_topics: list[str] = Field(default_factory=list)
    sql_topics: list[str] = Field(default_factory=list)
    suggested_topics: list[dict[str, str]] = Field(default_factory=list)


class PreparationPlanResponse(BaseModel):
    job_title: str = ""
    focus_label: str = ""
    total_days: int
    estimated_hours: float
    days: list[dict[str, Any]] = Field(default_factory=list)


class MockInterviewStartRequest(BaseModel):
    job_id: str = ""
    job_description: str = ""
    job_title: str = ""
    resume_id: str = ""
    category: str = "mixed"


class MockInterviewSessionResponse(BaseModel):
    session_id: str
    category: str
    round_label: str
    total_questions: int
    questions: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = ""


class MockCompleteRequest(BaseModel):
    job_id: str = ""
    session_id: str
    category: str = "mixed"


class PracticeRecordRequest(BaseModel):
    job_id: str = ""
    question_id: str
    question_text: str
    category: str = "technical"


class TopicCompleteRequest(BaseModel):
    job_id: str = ""
    topic: str


class PrepProgressResponse(BaseModel):
    practiced_questions: list[dict[str, Any]] = Field(default_factory=list)
    completed_topics: list[str] = Field(default_factory=list)
    mock_sessions_completed: int = 0
    weak_areas: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)


class CompanyPatternResponse(BaseModel):
    company: str = ""
    company_type: str = ""
    role_emphasis: str = ""
    frequent_topics: list[str] = Field(default_factory=list)
    role_specific_emphasis: list[str] = Field(default_factory=list)
    interview_trends: list[str] = Field(default_factory=list)


class InterviewPrepJobSummary(BaseModel):
    job_id: str
    application_id: str = ""
    title: str
    company: str = ""
    status: str = "saved"
    match_score: int = 0
    location: str = ""
    source: str = ""
    readiness_score: int = 0
    technical_readiness: int = 0
    behavioral_readiness: int = 0
    practiced_count: int = 0
    mock_sessions_completed: int = 0
    focus_label: str = ""


class InterviewPrepJobsResponse(BaseModel):
    jobs: list[InterviewPrepJobSummary] = Field(default_factory=list)
    total: int = 0
    filter: str = "all"


class InterviewPrepOverviewResponse(BaseModel):
    job_id: str = ""
    job_title: str = ""
    company: str = ""
    readiness: ReadinessResponse
    questions: QuestionsResponse
    topics: TopicsResponse
    technical_focus: TechnicalFocusResponse
    coding_topics: CodingTopicsResponse
    preparation_plan: PreparationPlanResponse
    company_patterns: CompanyPatternResponse
    progress: PrepProgressResponse
