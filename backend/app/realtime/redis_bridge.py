"""Optional Redis pub/sub bridge for cross-process realtime events."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.core.config import settings
from app.core.redis_client import get_redis
from app.realtime.websocket_manager import realtime_manager

logger = logging.getLogger(__name__)

REALTIME_CHANNEL = "career_os:realtime"


async def publish_realtime_event(user_id: str, payload: dict[str, Any]) -> None:
    """Publish to Redis so API workers can fan-out to WebSockets."""
    redis_client = get_redis()
    if not redis_client or not settings.REDIS_ENABLED:
        await realtime_manager.send_to_user(user_id, payload)
        return
    message = json.dumps({"user_id": user_id, "payload": payload}, default=str)
    try:
        redis_client.publish(REALTIME_CHANNEL, message)
    except Exception as exc:
        logger.debug("Redis publish fallback: %s", exc)
        await realtime_manager.send_to_user(user_id, payload)


async def start_realtime_subscriber() -> asyncio.Task | None:
    """Subscribe to Redis and forward events to in-process WebSocket pool."""
    if not settings.REDIS_ENABLED:
        return None

    redis_client = get_redis()
    if redis_client is None:
        return None

    async def _loop() -> None:
        pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(REALTIME_CHANNEL)
        logger.info("Realtime Redis subscriber started", extra={"event": "realtime_subscriber"})
        while True:
            message = pubsub.get_message(timeout=1.0)
            if not message or message.get("type") != "message":
                await asyncio.sleep(0.05)
                continue
            try:
                data = json.loads(message["data"])
                user_id = data.get("user_id", "")
                payload = data.get("payload", {})
                if user_id and payload:
                    await realtime_manager.send_to_user(user_id, payload)
            except Exception as exc:
                logger.warning("Realtime subscriber parse error: %s", exc)

    return asyncio.create_task(_loop())
