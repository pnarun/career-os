import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth.jwt_service import verify_access_token
from app.core.config import settings
from app.core.user_context import clear_request_user, set_request_user
from app.realtime.websocket_manager import realtime_manager
from app.services.user_service import UserNotFoundError, get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


async def _reject_websocket(websocket: WebSocket, code: int, reason: str) -> None:
    """Accept then close — closing before accept makes uvicorn log HTTP 403."""
    await websocket.accept()
    await websocket.close(code=code, reason=reason)


@router.websocket("/ws/realtime")
async def realtime_websocket(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """Authenticated WebSocket for user-scoped real-time events."""
    if not settings.ENABLE_REALTIME:
        logger.info("[REALTIME] connection rejected: realtime disabled by config")
        await _reject_websocket(websocket, 4503, "Realtime disabled")
        return

    if not token:
        logger.debug("[REALTIME] connection rejected: missing token")
        await _reject_websocket(websocket, 4401, "Missing token")
        return

    try:
        user_id = verify_access_token(token)
        user = await get_user_by_id(user_id)
        if not user.is_active:
            logger.warning("[REALTIME] connection rejected: inactive user=%s", user_id)
            await _reject_websocket(websocket, 4403, "Account disabled")
            return
    except ValueError as exc:
        logger.debug("[REALTIME] connection rejected: invalid token (%s)", exc)
        await _reject_websocket(websocket, 4401, "Invalid or expired token")
        return
    except UserNotFoundError:
        logger.debug("[REALTIME] connection rejected: user not found")
        await _reject_websocket(websocket, 4401, "Invalid token")
        return

    set_request_user(user.id, user.workspace_id, user.email)

    if realtime_manager.total_connections() >= settings.WEBSOCKET_MAX_CONNECTIONS_TOTAL:
        logger.warning("[REALTIME] connection rejected: global limit")
        await _reject_websocket(websocket, 4429, "Server busy — try again shortly")
        return

    if realtime_manager.connection_count(user.id) >= settings.WEBSOCKET_MAX_CONNECTIONS_PER_USER:
        logger.warning("[REALTIME] connection rejected: per-user limit user=%s", user_id)
        await _reject_websocket(websocket, 4429, "Too many tabs open")
        return

    await realtime_manager.connect(websocket, user.id)
    try:
        await websocket.send_json(
            {
                "event": "connected",
                "user_id": user_id,
                "message": "Real-time channel ready",
            }
        )
        while True:
            raw = await websocket.receive_text()
            if raw.strip().lower() == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception(
            "[REALTIME] websocket error user=%s",
            user_id,
            extra={"event": "websocket_error", "user_id": user_id},
        )
    finally:
        await realtime_manager.disconnect(websocket, user.id)
        clear_request_user()
