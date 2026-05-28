"""Optional MongoDB slow-query and aggregation timing helpers."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Callable
from typing import Any, TypeVar

from app.core.config import settings
from app.observability.operational_metrics import record_mongo_aggregation

logger = logging.getLogger(__name__)

T = TypeVar("T")


def slow_query_threshold_ms() -> float:
    return float(getattr(settings, "MONGO_SLOW_QUERY_MS", 500))


def log_slow_query(
    *,
    operation: str,
    collection: str,
    duration_ms: float,
    extra: dict[str, Any] | None = None,
) -> None:
    threshold = slow_query_threshold_ms()
    if duration_ms < threshold:
        return
    payload = {
        "event": "slow_query",
        "operation": operation,
        "collection": collection,
        "duration_ms": round(duration_ms, 2),
        **(extra or {}),
    }
    logger.warning(
        "SLOW_QUERY %s %s %.1fms",
        operation,
        collection,
        duration_ms,
        extra=payload,
    )


def log_aggregation_duration(
    *,
    name: str,
    duration_ms: float,
    stages: int | None = None,
) -> None:
    # "name" is reserved on logging.LogRecord — use aggregation_name in extra=
    payload: dict[str, Any] = {
        "event": "aggregation_duration",
        "aggregation_name": name,
        "duration_ms": round(duration_ms, 2),
    }
    if stages is not None:
        payload["stages"] = stages
    record_mongo_aggregation(name, duration_ms)
    logger.info(
        "AGGREGATION_DURATION name=%s duration_ms=%.1f",
        name,
        duration_ms,
        extra=payload,
    )
    if duration_ms >= slow_query_threshold_ms():
        logger.warning(
            "SLOW_QUERY aggregation %s %.1fms",
            name,
            duration_ms,
            extra={**payload, "event": "slow_query"},
        )


async def timed_to_list(
    cursor: Any,
    *,
    operation: str,
    collection: str,
    max_length: int | None = None,
) -> list[Any]:
    """Await cursor.to_list with SLOW_QUERY logging."""
    start = time.perf_counter()
    documents = await cursor.to_list(length=max_length)
    duration_ms = (time.perf_counter() - start) * 1000
    log_slow_query(
        operation=operation,
        collection=collection,
        duration_ms=duration_ms,
        extra={"documents": len(documents)},
    )
    return documents


async def timed_find_one(
    collection: Any,
    filter_query: dict[str, Any],
    *,
    operation: str,
    projection: dict[str, Any] | None = None,
    sort: list[tuple[str, int]] | None = None,
) -> dict[str, Any] | None:
    start = time.perf_counter()
    kwargs: dict[str, Any] = {}
    if projection is not None:
        kwargs["projection"] = projection
    if sort is not None:
        kwargs["sort"] = sort
    document = await collection.find_one(filter_query, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    log_slow_query(
        operation=operation,
        collection=collection.name,
        duration_ms=duration_ms,
        extra={"found": document is not None},
    )
    return document


async def run_timed(
    name: str,
    coro_factory: Callable[[], Any],
) -> T:
    """Time an awaitable factory (aggregation / multi-step reads)."""
    start = time.perf_counter()
    result = await coro_factory()
    duration_ms = (time.perf_counter() - start) * 1000
    log_aggregation_duration(name=name, duration_ms=duration_ms)
    return result


async def explain_find_if_debug(
    collection: Any,
    filter_query: dict[str, Any],
    *,
    sort: list[tuple[str, int]] | None = None,
) -> None:
    """Log COLLSCAN hints when MONGO_EXPLAIN_QUERIES is enabled."""
    if not getattr(settings, "MONGO_EXPLAIN_QUERIES", False):
        return
    try:
        cursor = collection.find(filter_query)
        if sort:
            cursor = cursor.sort(sort)
        plan = await cursor.explain()
        winning = (plan or {}).get("queryPlanner", {}).get("winningPlan", {})
        stage = winning.get("stage", "")
        if stage == "COLLSCAN":
            logger.warning(
                "Mongo COLLSCAN on %s filter=%s",
                collection.name,
                filter_query,
                extra={
                    "event": "mongo_collscan",
                    "collection": collection.name,
                },
            )
    except Exception as exc:
        logger.debug("explain failed: %s", exc)
