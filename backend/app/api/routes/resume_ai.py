"""Resume AI / ATS intelligence API routes."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.resume_ai import (
    AtsScoreResponse,
    JdAlignmentRequest,
    JdAlignmentResponse,
    KeywordOptimizationResponse,
    ResumeAiOverviewResponse,
    ResumeExportRequest,
    ResumeExportResponse,
    ResumeFeedbackResponse,
    ResumeVariantItem,
    ResumeVariantsResponse,
    SkillGapResponse,
    TailorResumeRequest,
    TailorResumeResponse,
)
from app.services.resume_ai.ats_scoring_service import compute_ats_score
from app.services.resume_ai.jd_resume_alignment import align_resume_to_job
from app.services.resume_ai.keyword_optimizer import analyze_keywords
from app.services.resume_ai.resume_ai_facade import (
    market_jobs_context,
    resolve_job_for_tailoring,
    resolve_resume,
)
from app.services.resume_ai.resume_export_service import export_resume
from app.services.resume_ai.resume_feedback_service import generate_resume_feedback
from app.services.resume_ai.resume_optimizer import optimize_resume_for_job
from app.services.resume_ai.resume_variant_service import generate_resume_variants
from app.services.resume_ai.skill_gap_service import analyze_skill_gaps
from app.services.resume_service import ResumeNotFoundError, ResumeServiceError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["resume-ai"])


async def _get_resume(resume_id: str = ""):
    try:
        return await resolve_resume(resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except ResumeServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc


@router.get("/resume-ai/overview", response_model=ResumeAiOverviewResponse)
async def get_resume_ai_overview(resume_id: str = Query(default="")) -> ResumeAiOverviewResponse:
    """Full Resume AI dashboard payload."""
    resume = await _get_resume(resume_id)
    market = await market_jobs_context()

    ats_raw = compute_ats_score(resume)
    feedback_raw = generate_resume_feedback(resume)
    keywords_raw = analyze_keywords(resume, market_jobs=market)
    gaps_raw = analyze_skill_gaps(resume, market_jobs=market)
    variants_raw = generate_resume_variants(resume)

    return ResumeAiOverviewResponse(
        resume_id=resume.id,
        resume_filename=resume.filename,
        ats=AtsScoreResponse(
            resume_id=resume.id,
            ats_score=ats_raw["ats_score"],
            keyword_score=ats_raw["keyword_score"],
            format_score=ats_raw["format_score"],
            skills_score=ats_raw["skills_score"],
            experience_score=ats_raw["experience_score"],
            factors=ats_raw["factors"],
            section_analysis=ats_raw.get("section_analysis", {}),
        ),
        feedback=ResumeFeedbackResponse(resume_id=resume.id, **feedback_raw),
        keywords=KeywordOptimizationResponse(resume_id=resume.id, **keywords_raw),
        skill_gaps=SkillGapResponse(resume_id=resume.id, **gaps_raw),
        variants=ResumeVariantsResponse(
            resume_id=resume.id,
            variants=[ResumeVariantItem(**v) for v in variants_raw["variants"]],
            recommended_variant=variants_raw["recommended_variant"],
            master_skill_count=variants_raw["master_skill_count"],
        ),
    )


@router.get("/resume-ai/ats-score", response_model=AtsScoreResponse)
async def get_ats_score(
    resume_id: str = Query(default=""),
    job_description: str = Query(default=""),
) -> AtsScoreResponse:
    resume = await _get_resume(resume_id)
    result = compute_ats_score(resume, job_description=job_description)
    return AtsScoreResponse(
        resume_id=resume.id,
        ats_score=result["ats_score"],
        keyword_score=result["keyword_score"],
        format_score=result["format_score"],
        skills_score=result["skills_score"],
        experience_score=result["experience_score"],
        factors=result["factors"],
        section_analysis=result.get("section_analysis", {}),
    )


@router.get("/resume-ai/feedback", response_model=ResumeFeedbackResponse)
async def get_resume_feedback(resume_id: str = Query(default="")) -> ResumeFeedbackResponse:
    resume = await _get_resume(resume_id)
    result = generate_resume_feedback(resume)
    return ResumeFeedbackResponse(resume_id=resume.id, **result)


@router.get("/resume-ai/keywords", response_model=KeywordOptimizationResponse)
async def get_keyword_optimization(resume_id: str = Query(default="")) -> KeywordOptimizationResponse:
    resume = await _get_resume(resume_id)
    market = await market_jobs_context()
    result = analyze_keywords(resume, market_jobs=market)
    return KeywordOptimizationResponse(resume_id=resume.id, **result)


@router.get("/resume-ai/skill-gaps", response_model=SkillGapResponse)
async def get_skill_gaps(resume_id: str = Query(default="")) -> SkillGapResponse:
    resume = await _get_resume(resume_id)
    market = await market_jobs_context()
    result = analyze_skill_gaps(resume, market_jobs=market)
    return SkillGapResponse(resume_id=resume.id, **result)


@router.get("/resume-ai/variants", response_model=ResumeVariantsResponse)
async def get_resume_variants(resume_id: str = Query(default="")) -> ResumeVariantsResponse:
    resume = await _get_resume(resume_id)
    result = generate_resume_variants(resume)
    return ResumeVariantsResponse(
        resume_id=resume.id,
        variants=[ResumeVariantItem(**v) for v in result["variants"]],
        recommended_variant=result["recommended_variant"],
        master_skill_count=result["master_skill_count"],
    )


@router.post("/resume-ai/align-job", response_model=JdAlignmentResponse)
async def post_align_job(payload: JdAlignmentRequest) -> JdAlignmentResponse:
    resume = await _get_resume(payload.resume_id)
    result = align_resume_to_job(
        resume,
        job_description=payload.job_description,
        job_title=payload.job_title,
        job_location=payload.job_location,
        job_remote=payload.job_remote,
    )
    return JdAlignmentResponse(resume_id=resume.id, **result)


@router.post("/resume-ai/tailor", response_model=TailorResumeResponse)
async def post_tailor_resume(payload: TailorResumeRequest) -> TailorResumeResponse:
    resume = await _get_resume(payload.resume_id)
    try:
        description, title, location, remote = await resolve_job_for_tailoring(
            job_id=payload.job_id,
            job_description=payload.job_description,
            job_title=payload.job_title,
            job_location=payload.job_location,
            job_remote=payload.job_remote,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    if len(description.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail={"message": "Job description too short for tailoring analysis"},
        )

    result = optimize_resume_for_job(
        resume,
        job_description=description,
        job_title=title,
        job_location=location,
        job_remote=remote,
    )
    return TailorResumeResponse(resume_id=resume.id, **result)


@router.post("/resume-ai/export", response_model=ResumeExportResponse)
async def post_export_resume(payload: ResumeExportRequest) -> ResumeExportResponse:
    resume = await _get_resume(payload.resume_id)
    exported = export_resume(
        resume,
        format=payload.format,
        variant_id=payload.variant_id,
    )
    return ResumeExportResponse(resume_id=resume.id, **exported)
