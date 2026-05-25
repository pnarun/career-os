import logging

from fastapi import APIRouter, HTTPException

from app.models.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotOverviewResponse,
    QuickActionRequest,
)
from app.services.copilot.career_chat_service import (
    get_copilot_overview,
    handle_chat,
    run_quick_action,
)
from app.services.copilot.insight_memory_service import get_recurring_themes, list_insight_history
from app.services.copilot.user_context_builder import build_user_context

logger = logging.getLogger(__name__)

router = APIRouter(tags=["copilot"])


@router.get("/copilot/overview", response_model=CopilotOverviewResponse)
async def copilot_overview() -> CopilotOverviewResponse:
    try:
        data = await get_copilot_overview()
        return CopilotOverviewResponse(**data)
    except Exception as exc:
        logger.exception("Failed to build copilot overview")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.post("/copilot/chat", response_model=CopilotChatResponse)
async def copilot_chat(payload: CopilotChatRequest) -> CopilotChatResponse:
    try:
        result = await handle_chat(
            payload.message,
            session_id=payload.session_id or None,
        )
        return CopilotChatResponse(**result)
    except Exception as exc:
        logger.exception("Copilot chat failed")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.post("/copilot/quick-action", response_model=CopilotChatResponse)
async def copilot_quick_action(payload: QuickActionRequest) -> CopilotChatResponse:
    try:
        result = await run_quick_action(
            payload.action_id,
            session_id=payload.session_id or None,
        )
        return CopilotChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Copilot quick action failed")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/copilot/context")
async def copilot_context() -> dict:
    try:
        return await build_user_context()
    except Exception as exc:
        logger.exception("Failed to build copilot context")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@router.get("/copilot/history")
async def copilot_history(limit: int = 30) -> dict:
    try:
        history = await list_insight_history(limit=limit)
        themes = await get_recurring_themes()
        return {"history": history, "recurring_themes": themes}
    except Exception as exc:
        logger.exception("Failed to fetch copilot history")
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc
