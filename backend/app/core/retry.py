"""Retry helpers with exponential backoff."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_sync(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    label: str = "operation",
) -> T:
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0, delay * 0.1)
            logger.warning(
                "%s failed attempt=%d/%d delay=%.2fs error=%s",
                label,
                attempt,
                max_attempts,
                delay,
                exc,
                extra={"event": "retry_scheduled", "status": "warning"},
            )
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    label: str = "operation",
) -> T:
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except retry_on as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0, delay * 0.1)
            logger.warning(
                "%s failed attempt=%d/%d delay=%.2fs error=%s",
                label,
                attempt,
                max_attempts,
                delay,
                exc,
                extra={"event": "retry_scheduled", "status": "warning"},
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
