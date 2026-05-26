"""In-memory ring buffer of recent application logs (for /logs viewer)."""

from __future__ import annotations

from collections import deque
from threading import Lock

LOG_BUFFER_MAX = 800

_lock = Lock()
_entries: deque[str] = deque(maxlen=LOG_BUFFER_MAX)


class LogBuffer:
    def append(self, line: str) -> None:
        if not line:
            return
        with _lock:
            _entries.append(line)

    def tail(self, limit: int = 200) -> list[str]:
        cap = max(1, min(limit, LOG_BUFFER_MAX))
        with _lock:
            return list(_entries)[-cap:]

    def clear(self) -> None:
        with _lock:
            _entries.clear()

    def __len__(self) -> int:
        with _lock:
            return len(_entries)


log_buffer = LogBuffer()
