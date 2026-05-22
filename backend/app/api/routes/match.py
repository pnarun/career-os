import logging

from fastapi import APIRouter, HTTPException

from app.models.match import MatchJobRequest, MatchJobResponse
from app.services.match_engine_service import match_resume_to_job
from app.services.resume_service import (
    ResumeNotFoundError,
    ResumeServiceError,
    get_all_resumes,
    get_resume_by_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["match"])


async def _resolve_resume(resume_id: str):
    if resume_id.strip():
        return await get_resume_by_id(resume_id.strip())

    resumes = await get_all_resumes()
    if not resumes:
        raise HTTPException(
            status_code=404,
            detail={"message": "No resumes found. Upload a resume first."},
        )
    return resumes[0]


@router.post("/match-job", response_model=MatchJobResponse)
async def match_job(request: MatchJobRequest) -> MatchJobResponse:
    """Match a stored resume profile against a job description."""
    try:
        resume = await _resolve_resume(request.resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"message": str(exc)},
        ) from exc
    except ResumeServiceError as exc:
        logger.error("Resume lookup failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "Unable to fetch resume for matching"},
        ) from exc

    analysis = match_resume_to_job(resume.skills, request.job_description)

    return MatchJobResponse(
        resume_id=resume.id,
        **analysis,
    )
