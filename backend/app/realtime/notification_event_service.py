import logging

from app.core.user_context import get_request_user_id
from app.models.notification import NotificationDocument
from app.realtime.websocket_manager import publish_user_event

logger = logging.getLogger(__name__)


async def _resolve_user_id(preference_id: str) -> str:
    user_id = get_request_user_id()
    if user_id:
        return user_id
    if not preference_id:
        return ""
    try:
        from app.services.user_preferences_service import get_preferences_by_id

        prefs = await get_preferences_by_id(preference_id)
        return prefs.user_id if prefs else ""
    except Exception:
        return ""


async def emit_notification_created(
    notification: NotificationDocument,
    *,
    user_id: str = "",
) -> None:
    target = user_id or await _resolve_user_id(notification.preference_id)
    if not target:
        return

    await publish_user_event(
        target,
        "notification",
        notification={
            "id": notification.id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "priority": notification.priority,
            "read": notification.read,
            "created_at": notification.created_at,
            "metadata": notification.metadata,
        },
    )


async def emit_unread_count(user_id: str, unread_count: int) -> None:
    if not user_id:
        return
    await publish_user_event(
        user_id,
        "unread_count",
        unread_count=unread_count,
    )
