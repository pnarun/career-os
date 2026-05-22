import logging

from fastapi import APIRouter, HTTPException

from app.core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(tags=["database"])


@router.get("/db-check")
async def db_check() -> dict[str, str]:
    """Ping MongoDB and confirm Atlas connectivity."""
    try:
        database = get_database()
        await database.client.admin.command("ping")
        return {"status": "connected"}
    except RuntimeError as exc:
        logger.error("Database not initialized: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": "Database not initialized"},
        ) from exc
    except Exception as exc:
        logger.exception("MongoDB ping failed")
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "message": "Unable to reach MongoDB"},
        ) from exc
