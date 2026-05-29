"""Background scan API — immediate response + Redis progress polling."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth.dependencies import CurrentUser, get_current_user
from app.models.scan_state import ScanStartRequest, ScanStartResponse, ScanStatusResponse
from app.scan_execution import scan_execution_manager
from app.services.scan_state_service import get_scan_state

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scans"])


def _to_status_response(state) -> ScanStatusResponse:
    return ScanStatusResponse(
        scan_id=state.scan_id,
        status=state.status,
        progress=state.progress,
        current_provider=state.current_provider,
        providers=state.providers,
        providers_completed=state.providers_completed,
        providers_failed=state.providers_failed,
        jobs_found=state.jobs_found,
        jobs_stored=state.jobs_stored,
        errors=state.errors,
        started_at=state.started_at,
        completed_at=state.completed_at,
        result_summary=state.result_summary,
    )


@router.post("/scans/start", response_model=ScanStartResponse)
async def start_background_scan(
    payload: ScanStartRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
) -> ScanStartResponse:
    """Start a scan in the background; poll GET /scans/status/{scan_id} for progress."""
    scan_id = await scan_execution_manager.submit_background_scan(
        background_tasks=background_tasks,
        user_id=current_user.user_id,
        workspace_id=current_user.workspace_id or "",
        email=current_user.email or "",
        resume_id=payload.resume_id,
        preferences_id=payload.preferences_id,
        send_email=payload.send_email,
    )

    return ScanStartResponse(scan_id=scan_id, status="started")


@router.get("/scans/status/{scan_id}", response_model=ScanStatusResponse)
async def get_background_scan_status(
    scan_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ScanStatusResponse:
    state = get_scan_state(scan_id, user_id=current_user.user_id)
    if state is None:
        raise HTTPException(status_code=404, detail={"message": "Scan not found"})
    return _to_status_response(state)
