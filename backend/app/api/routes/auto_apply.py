import logging

from fastapi import APIRouter, HTTPException

from app.models.auto_apply import (
    ApplyAnalytics,
    ApplyConfirmRequest,
    ApplySessionCreate,
    ApplySessionDocument,
)
from app.services.auto_apply.apply_history_service import get_apply_analytics
from app.services.auto_apply.orchestrator import (
    AutoApplyError,
    cancel_assisted_apply,
    confirm_assisted_apply,
    get_session_status,
    start_assisted_apply,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auto-apply"])


@router.post("/auto-apply/start", response_model=ApplySessionDocument)
async def post_start_auto_apply(payload: ApplySessionCreate) -> ApplySessionDocument:
    try:
        return await start_assisted_apply(payload)
    except AutoApplyError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Failed to start assisted apply")
        raise HTTPException(status_code=500, detail={"message": "Failed to start apply session"}) from exc


@router.get("/auto-apply/analytics/limits", response_model=ApplyAnalytics)
async def get_auto_apply_limits() -> ApplyAnalytics:
    return await get_apply_analytics()


@router.get("/auto-apply/{session_id}", response_model=ApplySessionDocument)
async def get_auto_apply_session(session_id: str) -> ApplySessionDocument:
    session = await get_session_status(session_id)
    if not session:
        raise HTTPException(status_code=404, detail={"message": "Apply session not found"})
    return session


@router.post("/auto-apply/{session_id}/confirm", response_model=ApplySessionDocument)
async def post_confirm_auto_apply(
    session_id: str,
    body: ApplyConfirmRequest | None = None,
) -> ApplySessionDocument:
    try:
        return await confirm_assisted_apply(session_id, body)
    except AutoApplyError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.post("/auto-apply/{session_id}/cancel", response_model=ApplySessionDocument)
async def post_cancel_auto_apply(session_id: str) -> ApplySessionDocument:
    try:
        return await cancel_assisted_apply(session_id)
    except AutoApplyError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
