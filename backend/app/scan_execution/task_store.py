"""MongoDB-backed scan task store with worker claim/reclaim safety."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings
from app.core.database import get_database
from app.scan_execution.models import ScanExecutionTask, ScanTaskKind, ScanTaskStatus

logger = logging.getLogger(__name__)

COLLECTION = "scan_execution_tasks"

_memory_store: dict[str, ScanExecutionTask] = {}


def _collection():
    return get_database()[COLLECTION]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def new_task_id() -> str:
    return f"stask_{uuid.uuid4().hex[:16]}"


async def insert_task(task: ScanExecutionTask) -> ScanExecutionTask:
    doc = task.to_mongo()
    try:
        await _collection().insert_one(doc)
        logger.info(
            "[SCAN_TASK] queued task_id=%s kind=%s user_id=%s scan_id=%s",
            task.task_id,
            task.kind.value,
            task.user_id,
            task.scan_id,
            extra={
                "event": "scan_task_queued",
                "task_id": task.task_id,
                "kind": task.kind.value,
                "user_id": task.user_id,
                "scan_id": task.scan_id,
            },
        )
    except Exception as exc:
        logger.warning(
            "scan_execution_tasks insert failed — using in-memory fallback: %s",
            exc,
            extra={"event": "scan_task_store_fallback", "task_id": task.task_id},
        )
        _memory_store[task.task_id] = task
    return task


async def update_task(
    task_id: str,
    *,
    status: ScanTaskStatus | None = None,
    error: str = "",
    error_summary: str = "",
    scan_id: str | None = None,
    result_summary: dict[str, Any] | None = None,
    claimed_at: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    worker_id: str | None = None,
    dispatch_latency_ms: float | None = None,
) -> None:
    patch: dict[str, Any] = {}
    if status is not None:
        patch["status"] = status.value
    if error:
        patch["error"] = error[:500]
    if error_summary:
        patch["error_summary"] = error_summary[:500]
    if scan_id is not None:
        patch["scan_id"] = scan_id
    if result_summary is not None:
        patch["result_summary"] = result_summary
    if claimed_at is not None:
        patch["claimed_at"] = claimed_at
    if started_at is not None:
        patch["started_at"] = started_at
    if completed_at is not None:
        patch["completed_at"] = completed_at
    if worker_id is not None:
        patch["worker_id"] = worker_id
    if dispatch_latency_ms is not None:
        patch["dispatch_latency_ms"] = dispatch_latency_ms

    if not patch:
        return

    if task_id in _memory_store:
        stored = _memory_store[task_id]
        _memory_store[task_id] = stored.model_copy(update=patch)
        return

    try:
        await _collection().update_one({"task_id": task_id}, {"$set": patch})
    except Exception as exc:
        logger.debug("scan task update failed task_id=%s: %s", task_id, exc)


async def get_task(task_id: str) -> ScanExecutionTask | None:
    if task_id in _memory_store:
        return _memory_store[task_id]
    try:
        doc = await _collection().find_one({"task_id": task_id})
        if doc:
            return ScanExecutionTask.from_mongo(doc)
    except Exception as exc:
        logger.debug("scan task get failed task_id=%s: %s", task_id, exc)
    return None


async def has_active_task_for_preference(
    preference_id: str,
    *,
    kind: ScanTaskKind | None = None,
) -> bool:
    if not preference_id:
        return False
    active = [s.value for s in ScanTaskStatus.active_statuses()]
    query: dict[str, Any] = {
        "preference_id": preference_id,
        "status": {"$in": active},
    }
    if kind is not None:
        query["kind"] = kind.value
    try:
        doc = await _collection().find_one(query, projection={"task_id": 1})
        return doc is not None
    except Exception:
        for task in _memory_store.values():
            if task.preference_id != preference_id:
                continue
            if task.status not in ScanTaskStatus.active_statuses():
                continue
            if kind is not None and task.kind != kind:
                continue
            return True
        return False


async def claim_next_queued_task(*, worker_id: str) -> ScanExecutionTask | None:
    """Atomically claim oldest queued task (queued → claimed)."""
    from pymongo import ReturnDocument

    claimed_at = _utc_now_iso()
    try:
        doc = await _collection().find_one_and_update(
            {"status": ScanTaskStatus.QUEUED.value},
            {
                "$set": {
                    "status": ScanTaskStatus.CLAIMED.value,
                    "worker_id": worker_id,
                    "claimed_at": claimed_at,
                }
            },
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if doc:
            task = ScanExecutionTask.from_mongo(doc)
            created = _parse_iso(task.created_at)
            latency_ms = None
            if created:
                latency_ms = round((_utc_now() - created).total_seconds() * 1000, 1)
                await update_task(task.task_id, dispatch_latency_ms=latency_ms)
                task.dispatch_latency_ms = latency_ms
            logger.info(
                "[SCAN_TASK] claimed task_id=%s worker_id=%s dispatch_latency_ms=%s",
                task.task_id,
                worker_id,
                latency_ms,
                extra={
                    "event": "scan_task_claimed",
                    "task_id": task.task_id,
                    "worker_id": worker_id,
                    "user_id": task.user_id,
                    "kind": task.kind.value,
                },
            )
            return task
    except Exception as exc:
        logger.debug("claim_next_queued_task mongo failed: %s", exc)

    for task_id, task in sorted(_memory_store.items(), key=lambda x: x[1].created_at):
        if task.status != ScanTaskStatus.QUEUED:
            continue
        updated = task.model_copy(
            update={
                "status": ScanTaskStatus.CLAIMED,
                "worker_id": worker_id,
                "claimed_at": claimed_at,
            }
        )
        _memory_store[task_id] = updated
        return updated
    return None


async def reclaim_stale_tasks() -> dict[str, int]:
    """
    Requeue stale claimed tasks; abandon stale running tasks.
    Simple recovery — no distributed locks.
    """
    now = _utc_now()
    claim_timeout = timedelta(seconds=float(settings.SCAN_TASK_CLAIM_TIMEOUT_SECONDS))
    exec_timeout = timedelta(seconds=float(settings.SCAN_TASK_EXECUTION_TIMEOUT_SECONDS))
    requeued = 0
    abandoned = 0

    try:
        cursor = _collection().find(
            {"status": {"$in": [ScanTaskStatus.CLAIMED.value, ScanTaskStatus.RUNNING.value]}}
        )
        async for doc in cursor:
            task = ScanExecutionTask.from_mongo(doc)
            ref_time = _parse_iso(task.started_at) or _parse_iso(task.claimed_at)
            if ref_time is None:
                continue
            age = now - ref_time.astimezone(timezone.utc)

            if task.status == ScanTaskStatus.CLAIMED and age > claim_timeout:
                await update_task(
                    task.task_id,
                    status=ScanTaskStatus.QUEUED,
                    worker_id="",
                    claimed_at="",
                    error_summary="reclaimed_stale_claim",
                )
                requeued += 1
                logger.warning(
                    "[SCAN_TASK] reclaimed stale claim task_id=%s age_s=%.0f",
                    task.task_id,
                    age.total_seconds(),
                    extra={"event": "scan_task_reclaimed", "task_id": task.task_id},
                )
            elif task.status == ScanTaskStatus.RUNNING and age > exec_timeout:
                await update_task(
                    task.task_id,
                    status=ScanTaskStatus.ABANDONED,
                    completed_at=_utc_now_iso(),
                    error_summary="execution_timeout",
                )
                abandoned += 1
                logger.warning(
                    "[SCAN_TASK] abandoned stale running task_id=%s age_s=%.0f",
                    task.task_id,
                    age.total_seconds(),
                    extra={"event": "scan_task_abandoned", "task_id": task.task_id},
                )
    except Exception as exc:
        logger.debug("reclaim_stale_tasks failed: %s", exc)

    return {"requeued": requeued, "abandoned": abandoned}


async def count_by_status(status: ScanTaskStatus) -> int:
    try:
        return await _collection().count_documents({"status": status.value})
    except Exception:
        return sum(1 for t in _memory_store.values() if t.status == status)


async def worker_queue_snapshot() -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in ScanTaskStatus:
        counts[status.value] = await count_by_status(status)
    return counts
