import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth.jwt_service import verify_access_token
from app.core.user_context import clear_request_user, set_request_user
from app.realtime.websocket_manager import realtime_manager
from app.services.user_service import UserNotFoundError, get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/realtime")
async def realtime_websocket(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """Authenticated WebSocket for user-scoped real-time events."""
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return

    try:
        user_id = verify_access_token(token)
        user = await get_user_by_id(user_id)
        if not user.is_active:
            await websocket.close(code=4403, reason="Account disabled")
            return
    except (ValueError, UserNotFoundError):
        await websocket.close(code=4401, reason="Invalid token")
        return

    set_request_user(user.id, user.workspace_id, user.email)

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
        logger.exception("[REALTIME] websocket error user=%s", user_id)
    finally:
        await realtime_manager.disconnect(websocket, user.id)
        clear_request_user()
