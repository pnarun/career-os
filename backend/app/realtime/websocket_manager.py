import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RealtimeConnectionManager:
    """User-scoped WebSocket connection pool."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)
        logger.info("[REALTIME] user=%s connected (total=%d)", user_id, len(self._connections[user_id]))

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        async with self._lock:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info("[REALTIME] user=%s disconnected", user_id)

    def connection_count(self, user_id: str) -> int:
        return len(self._connections.get(user_id, set()))

    def total_connections(self) -> int:
        return sum(len(sockets) for sockets in self._connections.values())

    async def send_to_user(self, user_id: str, payload: dict[str, Any]) -> int:
        if not user_id:
            return 0
        sockets = list(self._connections.get(user_id, set()))
        if not sockets:
            return 0

        sent = 0
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
                sent += 1
            except Exception:
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws, user_id)
        return sent

    async def broadcast(self, payload: dict[str, Any]) -> int:
        total = 0
        for user_id in list(self._connections.keys()):
            total += await self.send_to_user(user_id, payload)
        return total


realtime_manager = RealtimeConnectionManager()


async def publish_user_event(user_id: str, event: str, **data: Any) -> int:
    """Publish a lightweight event to all sockets for a user."""
    if not user_id:
        return 0
    payload: dict[str, Any] = {
        "event": event,
        "timestamp": _utc_now_iso(),
        **data,
    }
    return await realtime_manager.send_to_user(user_id, payload)
