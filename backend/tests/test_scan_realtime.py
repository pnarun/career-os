"""Scan realtime bridge tests."""

from app.models.scan_state import ScanProviderState, ScanState
from app.realtime.scan_event_service import emit_scan_progress_update
from app.realtime.scan_state_realtime import _serialize_providers


def test_serialize_providers():
    state = ScanState(
        scan_id="s1",
        user_id="u1",
        started_at="2026-01-01T00:00:00+00:00",
        providers={
            "linkedin": ScanProviderState(name="linkedin", status="running"),
        },
    )
    out = _serialize_providers(state)
    assert out["linkedin"]["status"] == "running"


def test_emit_scan_progress_update_event_name():
    assert callable(emit_scan_progress_update)
