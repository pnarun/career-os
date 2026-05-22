import logging

from fastapi import APIRouter, HTTPException, Query

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
) -> UserPreferencesDocument:
    try:
        saved = await save_preferences(payload)
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
async def read_preferences() -> UserPreferencesDocument | None:
    try:
        return await get_preferences()
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
) -> UserPreferencesDocument:
    try:
        updated = await update_preferences(preference_id, payload)
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
