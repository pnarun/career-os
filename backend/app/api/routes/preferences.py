import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import CurrentUser, get_current_user
from app.models.user_preferences import (
    UserPreferencesCreate,
    UserPreferencesDocument,
    UserPreferencesUpdate,
)
from app.services.scheduler_service import sync_preference_schedule
from app.services.user_preferences_service import (
    UserPreferencesNotFoundError,
    UserPreferencesServiceError,
    get_preferences,
    save_preferences,
    update_preferences,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["preferences"])


@router.post("/preferences", response_model=UserPreferencesDocument)
async def create_preferences(
    payload: UserPreferencesCreate,
    current_user: CurrentUser = Depends(get_current_user),
) -> UserPreferencesDocument:
    try:
        saved = await save_preferences(
            payload,
            user_id=current_user.user_id,
            workspace_id=current_user.workspace_id,
        )
        await sync_preference_schedule(saved)
        return saved
    except UserPreferencesServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error saving preferences")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.get("/preferences", response_model=UserPreferencesDocument | None)
async def read_preferences(
    current_user: CurrentUser = Depends(get_current_user),
) -> UserPreferencesDocument | None:
    try:
        return await get_preferences(current_user.user_id)
    except UserPreferencesServiceError as exc:
        raise HTTPException(status_code=503, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error reading preferences")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc


@router.put("/preferences", response_model=UserPreferencesDocument)
async def patch_preferences(
    payload: UserPreferencesUpdate,
    preference_id: str = Query(..., description="MongoDB preferences document id"),
    current_user: CurrentUser = Depends(get_current_user),
) -> UserPreferencesDocument:
    try:
        updated = await update_preferences(
            preference_id,
            payload,
            user_id=current_user.user_id,
        )
        await sync_preference_schedule(updated)
        return updated
    except UserPreferencesNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except UserPreferencesServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Unexpected error updating preferences")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred"},
        ) from exc
