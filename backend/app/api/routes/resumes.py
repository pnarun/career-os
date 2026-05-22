import logging

from fastapi import APIRouter, HTTPException

from app.models.resume import ResumeDocument
from app.services.resume_service import ResumeServiceError, get_all_resumes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["resumes"])


@router.get("/resumes", response_model=list[ResumeDocument])
async def list_resumes() -> list[ResumeDocument]:
    """List uploaded resumes (newest first) for settings resume picker."""
    try:
        return await get_all_resumes()
    except ResumeServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error listing resumes")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc
