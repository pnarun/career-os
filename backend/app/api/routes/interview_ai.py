"""Interview AI / career preparation API routes."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.interview_ai import (
    CodingTopicsResponse,
    CompanyPatternResponse,
    InterviewJobRequest,
    InterviewPrepJobsResponse,
    InterviewPrepJobSummary,
    InterviewPrepOverviewResponse,
    InterviewQuestionItem,
    MockCompleteRequest,
    MockInterviewSessionResponse,
    MockInterviewStartRequest,
    PracticeRecordRequest,
    PrepProgressResponse,
    PreparationPlanResponse,
    QuestionsResponse,
    ReadinessResponse,
    TechnicalFocusResponse,
    TopicCompleteRequest,
    TopicsResponse,
)
from app.services.interview_ai.behavioral_analyzer import analyze_behavioral_focus
from app.services.interview_ai.coding_topic_mapper import map_coding_topics
from app.services.interview_ai.company_pattern_service import analyze_company_patterns
from app.services.interview_ai.interview_ai_facade import (
    market_jobs_context,
    resolve_job_context,
    resolve_resume,
)
from app.services.interview_ai.interview_prep_jobs_service import list_interview_prep_jobs
from app.services.interview_ai.interview_question_generator import (
    generate_questions_with_web,
)
from app.services.interview_ai.interview_readiness_service import compute_readiness
from app.services.interview_ai.jd_topic_extractor import extract_topics
from app.services.interview_ai.mock_interview_service import get_random_practice_question, start_mock_session
from app.services.interview_ai.prep_progress_service import (
    get_progress,
    record_mock_complete,
    record_practice,
    record_topic_complete,
)
from app.services.interview_ai.preparation_plan_service import generate_preparation_plan
from app.services.interview_ai.technical_focus_service import analyze_technical_focus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["interview-ai"])


async def _resolve_jd(payload: InterviewJobRequest) -> tuple[str, str, str, str]:
    try:
        return await resolve_job_context(
            job_id=payload.job_id,
            job_description=payload.job_description,
            job_title=payload.job_title,
            company=payload.company,
            job_location=payload.job_location,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


def _questions_response(job_id: str, raw: dict) -> QuestionsResponse:
    def _items(items: list[dict]) -> list[InterviewQuestionItem]:
        return [
            InterviewQuestionItem(
                question=q.get("question", ""),
                topic=q.get("topic", ""),
                category=q.get("category", ""),
                tip=q.get("tip", ""),
                source=q.get("source", ""),
            )
            for q in items
        ]

    return QuestionsResponse(
        job_id=job_id,
        focus_label=raw.get("focus_label", ""),
        question_source=raw.get("question_source", "static"),
        technical_questions=_items(raw.get("technical_questions", [])),
        behavioral_questions=_items(raw.get("behavioral_questions", [])),
        system_design_prompts=_items(raw.get("system_design_prompts", [])),
        project_questions=_items(raw.get("project_questions", [])),
        resume_based_questions=_items(raw.get("resume_based_questions", [])),
        total_count=raw.get("total_count", 0),
    )


@router.get("/interview-prep/jobs", response_model=InterviewPrepJobsResponse)
async def get_interview_prep_jobs(
    status_filter: str = Query(default="all", alias="filter"),
) -> InterviewPrepJobsResponse:
    """List saved/applied jobs with readiness summaries for job picker."""
    if status_filter not in ("all", "saved", "applied", "interview"):
        status_filter = "all"
    result = await list_interview_prep_jobs(status_filter=status_filter)
    return InterviewPrepJobsResponse(
        jobs=[InterviewPrepJobSummary(**j) for j in result["jobs"]],
        total=result["total"],
        filter=result["filter"],
    )


@router.get("/interview-prep/overview", response_model=InterviewPrepOverviewResponse)
async def get_interview_prep_overview(
    job_id: str = Query(default=""),
    job_description: str = Query(default=""),
    job_title: str = Query(default=""),
    company: str = Query(default=""),
    resume_id: str = Query(default=""),
) -> InterviewPrepOverviewResponse:
    payload = InterviewJobRequest(
        job_id=job_id,
        job_description=job_description,
        job_title=job_title,
        company=company,
        resume_id=resume_id,
    )

    if not job_id.strip() and len(job_description.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail={"message": "Select a saved or applied job to view interview prep."},
        )

    description, title, comp, _loc = await _resolve_jd(payload)

    resume = await resolve_resume(resume_id)
    progress = await get_progress(job_id)
    market = await market_jobs_context()

    readiness_raw = compute_readiness(
        description,
        job_title=title,
        resume=resume,
        practiced_count=len(progress.get("practiced_questions", [])),
        completed_topics=len(progress.get("completed_topics", [])),
    )
    questions_raw = await generate_questions_with_web(
        description,
        job_id=job_id,
        job_title=title,
        company=comp,
        resume_text=resume.raw_text if resume else "",
        resume_skills=resume.skills if resume else [],
    )
    topics_raw = extract_topics(description, job_title=title, company=comp)
    focus_raw = analyze_technical_focus(description, job_title=title)
    coding_raw = map_coding_topics(description, job_title=title)
    plan_raw = generate_preparation_plan(description, job_title=title)
    patterns_raw = analyze_company_patterns(
        company=comp,
        job_title=title,
        job_description=description,
        market_jobs=market,
    )

    return InterviewPrepOverviewResponse(
        job_id=job_id,
        job_title=title,
        company=comp,
        readiness=ReadinessResponse(
            resume_id=resume.id if resume else None,
            job_id=job_id,
            **readiness_raw,
        ),
        questions=_questions_response(job_id, questions_raw),
        topics=TopicsResponse(job_id=job_id, **{k: v for k, v in topics_raw.items() if k in TopicsResponse.model_fields}),
        technical_focus=TechnicalFocusResponse(**focus_raw),
        coding_topics=CodingTopicsResponse(**{k: v for k, v in coding_raw.items() if k in CodingTopicsResponse.model_fields}),
        preparation_plan=PreparationPlanResponse(**plan_raw),
        company_patterns=CompanyPatternResponse(**{k: v for k, v in patterns_raw.items() if k in CompanyPatternResponse.model_fields}),
        progress=PrepProgressResponse(**progress),
    )


@router.post("/interview-prep/readiness", response_model=ReadinessResponse)
async def post_readiness(payload: InterviewJobRequest) -> ReadinessResponse:
    description, title, _, _ = await _resolve_jd(payload)
    resume = await resolve_resume(payload.resume_id)
    progress = await get_progress(payload.job_id)
    result = compute_readiness(
        description,
        job_title=title,
        resume=resume,
        practiced_count=len(progress.get("practiced_questions", [])),
        completed_topics=len(progress.get("completed_topics", [])),
    )
    return ReadinessResponse(
        resume_id=resume.id if resume else None,
        job_id=payload.job_id,
        **result,
    )


@router.post("/interview-prep/questions", response_model=QuestionsResponse)
async def post_questions(payload: InterviewJobRequest) -> QuestionsResponse:
    description, title, _, _ = await _resolve_jd(payload)
    resume = await resolve_resume(payload.resume_id)
    raw = await generate_questions_with_web(
        description,
        job_id=payload.job_id,
        job_title=title,
        company=payload.company,
        resume_text=resume.raw_text if resume else "",
        resume_skills=resume.skills if resume else [],
    )
    return _questions_response(payload.job_id, raw)


@router.post("/interview-prep/plan", response_model=PreparationPlanResponse)
async def post_preparation_plan(payload: InterviewJobRequest) -> PreparationPlanResponse:
    description, title, _, _ = await _resolve_jd(payload)
    return PreparationPlanResponse(**generate_preparation_plan(description, job_title=title))


@router.post("/interview-prep/mock/start", response_model=MockInterviewSessionResponse)
async def post_mock_start(payload: MockInterviewStartRequest) -> MockInterviewSessionResponse:
    description = payload.job_description
    title = payload.job_title
    if payload.job_id.strip():
        description, title, _, _ = await resolve_job_context(
            job_id=payload.job_id,
            job_description=payload.job_description,
            job_title=payload.job_title,
        )
    if len(description.strip()) < 10:
        description = "Software engineer role requiring backend, APIs, databases, and system design."

    resume = await resolve_resume(payload.resume_id)
    session = start_mock_session(
        description,
        job_title=title,
        resume_text=resume.raw_text if resume else "",
        category=payload.category,
    )
    return MockInterviewSessionResponse(**session)


@router.get("/interview-prep/mock/random")
async def get_random_question(category: str = Query(default="mixed")) -> dict:
    return get_random_practice_question(category)


@router.post("/interview-prep/mock/complete", response_model=PrepProgressResponse)
async def post_mock_complete(payload: MockCompleteRequest) -> PrepProgressResponse:
    progress = await record_mock_complete(
        job_id=payload.job_id,
        session_id=payload.session_id,
        category=payload.category,
    )
    return PrepProgressResponse(**progress)


@router.post("/interview-prep/practice", response_model=PrepProgressResponse)
async def post_record_practice(payload: PracticeRecordRequest) -> PrepProgressResponse:
    progress = await record_practice(
        job_id=payload.job_id,
        question_id=payload.question_id,
        question_text=payload.question_text,
        category=payload.category,
    )
    return PrepProgressResponse(**progress)


@router.post("/interview-prep/topic-complete", response_model=PrepProgressResponse)
async def post_topic_complete(payload: TopicCompleteRequest) -> PrepProgressResponse:
    progress = await record_topic_complete(job_id=payload.job_id, topic=payload.topic)
    return PrepProgressResponse(**progress)


@router.get("/interview-prep/progress", response_model=PrepProgressResponse)
async def get_prep_progress(job_id: str = Query(default="")) -> PrepProgressResponse:
    progress = await get_progress(job_id)
    return PrepProgressResponse(**progress)
