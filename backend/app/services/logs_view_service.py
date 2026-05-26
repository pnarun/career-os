"""Parse and filter in-memory API logs for /logs viewer."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from app.core.log_buffer import log_buffer


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_timestamp_human(ts: str) -> str:
    dt = _parse_iso(ts)
    if not dt:
        return ts or "—"
    local = dt.astimezone(timezone.utc)
    return local.strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_log_line(line: str) -> dict[str, Any]:
    try:
        data = json.loads(line)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {
        "timestamp": "",
        "user": "system",
        "level": "INFO",
        "message": line,
        "event": "",
        "logger": "",
    }


def log_line_summary(entry: dict[str, Any]) -> str:
    parts = [
        entry.get("message", ""),
        f"event={entry.get('event')}" if entry.get("event") else "",
        f"logger={entry.get('logger')}" if entry.get("logger") else "",
    ]
    return " · ".join(p for p in parts if p)


def get_log_entries(
    *,
    limit: int = 200,
    user_filter: str = "",
    level_filter: str = "",
) -> list[dict[str, Any]]:
    lines = log_buffer.tail(limit)
    entries: list[dict[str, Any]] = []
    user_needle = (user_filter or "").strip().lower()
    level_needle = (level_filter or "").strip().upper()

    for raw in lines:
        entry = parse_log_line(raw)
        user = str(entry.get("user") or "system")
        level = str(entry.get("level") or "INFO").upper()
        if user_needle and user_needle not in user.lower():
            continue
        if level_needle and level != level_needle:
            continue
        ts = str(entry.get("timestamp") or "")
        entries.append({
            "timestamp": ts,
            "timestamp_human": format_timestamp_human(ts),
            "user": user,
            "level": level,
            "message": log_line_summary(entry),
            "raw": entry,
        })
    return entries


def distinct_users(entries: list[dict[str, Any]]) -> list[str]:
    users = sorted({e["user"] for e in entries if e.get("user")})
    return users


def export_logs_csv(entries: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "timestamp_utc_human", "user", "level", "log"])
    for e in entries:
        writer.writerow([
            e.get("timestamp", ""),
            e.get("timestamp_human", ""),
            e.get("user", ""),
            e.get("level", ""),
            e.get("message", ""),
        ])
    return buf.getvalue()
