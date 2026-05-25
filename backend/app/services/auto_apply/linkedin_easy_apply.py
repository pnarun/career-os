"""LinkedIn Easy Apply — assisted, human-in-the-loop automation."""

from __future__ import annotations

import logging
import random
import time
from typing import Any

from app.automation.browser.screenshot_service import capture_page_sync, screenshot_relative_path
from app.automation.browser.session_status_service import is_session_ready
from app.automation.browser.sync_runner import close_browser_sync, create_context_sync
from app.models.auto_apply import DetectedQuestion, FilledField
from app.services.auto_apply.apply_history_service import sync_update_apply_session
from app.services.auto_apply.captcha_detector import detect_captcha
from app.services.auto_apply.confirmation_service import (
    clear_apply_flags,
    is_apply_cancelled,
    wait_for_confirmation,
)
from app.services.auto_apply.form_detector import (
    LINKEDIN_EASY_APPLY_SELECTORS,
    detect_form_fields,
    detect_linkedin_apply_type,
    detect_resume_upload,
)
from app.services.auto_apply.question_handler import build_apply_preferences, resolve_question
from app.services.auto_apply.resume_autofill import (
    autofill_fields,
    build_autofill_profile,
    compute_confidence_score,
)
from app.services.resume_service import get_resume_by_id_sync

logger = logging.getLogger(__name__)

PLATFORM = "linkedin"

APPLY_UI_SELECTORS = (
    ".jobs-easy-apply-modal",
    ".jobs-easy-apply-content",
    "motion.div.artdeco-modal--layer-default",
    "div.artdeco-modal--layer-default",
    "div[data-test-modal-id='easy-apply-modal']",
    "button[aria-label='Submit application']",
    "button[aria-label='Continue to next step']",
)


def _human_delay(min_ms: float = 400, max_ms: float = 900) -> None:
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)


def _update_state(session_id: str, state: str, **extra: Any) -> None:
    sync_update_apply_session(session_id, {"state": state, **extra})


def _log_step(message: str) -> None:
    logger.info("[LINKEDIN_EASY_APPLY] %s", message)
    print(f"[WORKER][EASY_APPLY] {message}", flush=True)


def _is_apply_ui_visible(page: Any) -> bool:
    for selector in APPLY_UI_SELECTORS:
        try:
            loc = page.locator(selector)
            if loc.count() > 0 and loc.first.is_visible():
                return True
        except Exception:
            continue
    try:
        if page.locator("input[type='file']").count() > 0:
            return True
    except Exception:
        pass
    return False


def _dismiss_blocking_overlays(page: Any) -> None:
    """Close cookie banners / overlays that intercept clicks."""
    for label in ("Accept", "Accept all", "Allow all", "Dismiss", "Close"):
        try:
            btn = page.get_by_role("button", name=label)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click(timeout=1500)
                _human_delay(300, 600)
        except Exception:
            pass


def _wait_for_job_page(page: Any) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=20000)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=12000)
    except Exception:
        pass
    for selector in ("#jobs-apply-button-id", "button.jobs-apply-button", "h1.t-24"):
        try:
            page.wait_for_selector(selector, timeout=10000, state="visible")
            return
        except Exception:
            continue
    _human_delay(1500, 2500)


def _js_click_apply_button(page: Any) -> bool:
    """DOM click bypasses some overlay interception issues."""
    try:
        clicked = page.evaluate(
            """() => {
                const btn = document.querySelector('#jobs-apply-button-id')
                    || document.querySelector('button.jobs-apply-button')
                    || [...document.querySelectorAll('button')].find(
                        b => (b.innerText || '').toLowerCase().includes('easy apply')
                    );
                if (!btn) return false;
                btn.scrollIntoView({ block: 'center' });
                btn.click();
                return true;
            }"""
        )
        return bool(clicked)
    except Exception:
        return False


def _click_easy_apply(page: Any) -> bool:
    _dismiss_blocking_overlays(page)

    strategies: list[tuple[str, Any]] = []

    def _try_js() -> None:
        if not _js_click_apply_button(page):
            raise RuntimeError("JS click found no button")

    strategies.append(("javascript click", _try_js))

    def _try_role() -> None:
        btn = page.get_by_role("button", name="Easy Apply")
        if btn.count() == 0:
            raise RuntimeError("No role=button Easy Apply")
        target = btn.first
        target.scroll_into_view_if_needed(timeout=5000)
        target.click(timeout=8000, force=True)

    strategies.append(("role=button", _try_role))

    for selector in LINKEDIN_EASY_APPLY_SELECTORS:
        def _try_sel(sel=selector) -> None:
            loc = page.locator(sel)
            if loc.count() == 0:
                raise RuntimeError(f"Missing {sel}")
            btn = loc.first
            if not btn.is_visible():
                raise RuntimeError(f"Not visible {sel}")
            btn.scroll_into_view_if_needed(timeout=5000)
            btn.click(timeout=8000, force=True)

        strategies.append((selector, _try_sel))

    def _try_mouse() -> None:
        loc = page.locator("#jobs-apply-button-id, button.jobs-apply-button")
        if loc.count() == 0:
            raise RuntimeError("No button for mouse click")
        box = loc.first.bounding_box()
        if not box:
            raise RuntimeError("No bounding box")
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    strategies.append(("mouse coordinates", _try_mouse))

    for label, action in strategies:
        try:
            _log_step(f"Click strategy: {label}")
            action()
            for wait_ms in (500, 1000, 1500, 2000):
                _human_delay(wait_ms, wait_ms + 200)
                if _is_apply_ui_visible(page):
                    _log_step(f"Apply UI open via {label}")
                    return True
        except Exception as exc:
            _log_step(f"Strategy failed ({label}): {exc}")

    return False


def _page_is_alive(page: Any) -> bool:
    try:
        return not page.is_closed()
    except Exception:
        return False


def _safe_capture(page: Any, *, label: str) -> str | None:
    if not _page_is_alive(page):
        return None
    try:
        shot = capture_page_sync(page, platform=PLATFORM, label=label)
        return screenshot_relative_path(shot)
    except Exception as exc:
        _log_step(f"Screenshot skipped ({label}): {exc}")
        return None


def _wait_for_manual_apply(page: Any, session_id: str, *, timeout_sec: int = 120) -> bool:
    """Human-in-the-loop: user clicks Easy Apply in the headed browser."""
    _log_step(
        "Auto-click failed — click Easy Apply manually in the browser window (120s). "
        "Do not close that browser tab."
    )
    sync_update_apply_session(
        session_id,
        {
            "state": "WAITING_CONFIRMATION",
            "confirmation_required": True,
            "metadata": {"manual_click_required": True},
        },
    )
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if is_apply_cancelled(session_id):
            return False
        if not _page_is_alive(page):
            _log_step("Browser tab was closed — session cancelled")
            return False
        if _is_apply_ui_visible(page):
            _log_step("Apply UI detected after manual click")
            return True
        time.sleep(1.5)
    return False


def _fill_text_inputs(page: Any, filled_fields: list[FilledField]) -> int:
    filled_count = 0
    for field in filled_fields:
        if not field.value:
            continue
        try:
            for selector in (
                f"input[aria-label*='{field.label[:20]}']",
                "input[type='text']:visible",
                "input[type='email']:visible",
                "input[type='tel']:visible",
            ):
                loc = page.locator(selector)
                if loc.count() == 0:
                    continue
                for i in range(min(loc.count(), 5)):
                    el = loc.nth(i)
                    if not el.is_visible():
                        continue
                    try:
                        current = el.input_value(timeout=1000)
                    except Exception:
                        current = ""
                    if current and current.strip():
                        continue
                    el.fill(field.value, timeout=3000)
                    filled_count += 1
                    _human_delay()
                    break
        except Exception:
            continue
    return filled_count


def _advance_form_steps(page: Any, max_steps: int = 5) -> None:
    for _ in range(max_steps):
        clicked = False
        for label in ("Continue to next step", "Review", "Next"):
            try:
                btn = page.locator(f"button[aria-label='{label}']")
                if btn.count() > 0 and btn.first.is_visible():
                    btn.first.click(timeout=3000)
                    _human_delay(800, 1500)
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            break


def _submit_application(page: Any) -> bool:
    for label in ("Submit application", "Submit", "Send application"):
        try:
            btn = page.locator(f"button[aria-label='{label}']")
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click(timeout=5000)
                _human_delay(1000, 2000)
                return True
        except Exception:
            continue
    return False


def linkedin_easy_apply_sync(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = payload.get("session_id", "")
    job_url = payload.get("job_url", "")
    resume_id = payload.get("resume_id", "")
    preferences = payload.get("apply_preferences") or {}

    if not session_id or not job_url:
        return {"status": "error", "message": "session_id and job_url required"}

    if not is_session_ready(PLATFORM):
        _update_state(session_id, "FAILED", error="LinkedIn session not ready")
        return {"status": "error", "message": "LinkedIn session not ready. Prepare session first."}

    clear_apply_flags(session_id)
    screenshots: list[str] = []

    try:
        _update_state(session_id, "OPENING_JOB")
        context = create_context_sync(
            platform=PLATFORM,
            headless=False,
            use_saved_session=True,
        )
        page = context.new_page()
        page.set_viewport_size({"width": 1400, "height": 900})
        page.set_default_timeout(30000)

        _log_step(f"Opening job URL: {job_url}")
        page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
        _wait_for_job_page(page)
        _dismiss_blocking_overlays(page)
        _log_step(f"Loaded: {page.url}")

        captcha, reason = detect_captcha(page)
        if captcha:
            shot = capture_page_sync(page, platform=PLATFORM, label="captcha_detected")
            screenshots.append(screenshot_relative_path(shot))
            _update_state(session_id, "CAPTCHA_BLOCKED", error=reason, screenshots=screenshots)
            close_browser_sync()
            return {"status": "captcha_blocked", "message": reason, "session_id": session_id}

        _update_state(session_id, "DETECTING_FORM")
        form_info = detect_linkedin_apply_type(page)
        _log_step(f"Detected easy_apply={form_info.is_easy_apply}")

        if not form_info.is_easy_apply:
            fail_shot = capture_page_sync(page, platform=PLATFORM, label="no_easy_apply")
            screenshots.append(screenshot_relative_path(fail_shot))
            _update_state(session_id, "FAILED", error="Easy Apply not available", screenshots=screenshots)
            close_browser_sync()
            return {"status": "error", "message": "Easy Apply not detected.", "session_id": session_id}

        apply_opened = _click_easy_apply(page)
        if not apply_opened:
            apply_opened = _wait_for_manual_apply(page, session_id, timeout_sec=120)

        if not apply_opened:
            fail_path = _safe_capture(page, label="easy_apply_click_failed")
            if fail_path:
                screenshots.append(fail_path)
            err = (
                "Could not open Easy Apply. The automation browser may have been closed, "
                "or LinkedIn did not show the apply form."
            )
            _update_state(session_id, "FAILED", error=err, screenshots=screenshots)
            close_browser_sync()
            return {"status": "error", "message": err, "session_id": session_id}

        shot_path = _safe_capture(page, label="form_detected")
        if shot_path:
            screenshots.append(shot_path)

        resume = get_resume_by_id_sync(resume_id) if resume_id else None
        profile = build_autofill_profile(resume) if resume else {}
        apply_prefs = build_apply_preferences(**preferences)

        if detect_resume_upload(page):
            _update_state(session_id, "UPLOADING_RESUME", screenshots=screenshots)

        _update_state(session_id, "FILLING_FIELDS", screenshots=screenshots)
        detected = detect_form_fields(page)
        filled = autofill_fields(detected, profile)
        _fill_text_inputs(page, filled)

        _update_state(session_id, "DETECTING_QUESTIONS")
        questions: list[DetectedQuestion] = []
        unknown: list[str] = []
        for field in detected:
            q = resolve_question(field.label, field.field_type, profile=profile, preferences=apply_prefs)
            questions.append(q)
            if q.requires_confirmation and not q.answered:
                unknown.append(q.label)

        confidence = compute_confidence_score(filled, len(unknown))
        _advance_form_steps(page)

        before_shot = capture_page_sync(page, platform=PLATFORM, label="before_submit")
        screenshots.append(screenshot_relative_path(before_shot))

        _update_state(
            session_id,
            "WAITING_CONFIRMATION",
            filled_fields=[f.model_dump() for f in filled],
            detected_questions=[q.model_dump() for q in questions],
            unknown_questions=unknown,
            confidence_score=confidence,
            confirmation_required=True,
            screenshots=screenshots,
            metadata={"apply_type": form_info.apply_type},
        )

        confirmation = wait_for_confirmation(session_id, timeout_sec=600)

        if confirmation == "cancelled":
            _update_state(session_id, "CANCELLED", screenshots=screenshots)
            close_browser_sync()
            return {"status": "cancelled", "session_id": session_id}

        if confirmation == "timeout":
            _update_state(
                session_id,
                "FAILED",
                error="Confirmation timeout — application not submitted",
                screenshots=screenshots,
            )
            close_browser_sync()
            return {"status": "error", "message": "Confirmation timeout", "session_id": session_id}

        captcha, reason = detect_captcha(page)
        if captcha:
            shot = capture_page_sync(page, platform=PLATFORM, label="captcha_before_submit")
            screenshots.append(screenshot_relative_path(shot))
            _update_state(session_id, "CAPTCHA_BLOCKED", error=reason, screenshots=screenshots)
            close_browser_sync()
            return {"status": "captcha_blocked", "message": reason, "session_id": session_id}

        _update_state(session_id, "SUBMITTING", confirmed=True, screenshots=screenshots)
        submitted = _submit_application(page)

        if submitted:
            success_shot = capture_page_sync(page, platform=PLATFORM, label="success")
            screenshots.append(screenshot_relative_path(success_shot))
            _update_state(session_id, "SUCCESS", submitted=True, screenshots=screenshots)
            close_browser_sync()
            return {"status": "ok", "session_id": session_id, "submitted": True, "screenshots": screenshots}

        _update_state(session_id, "FAILED", error="Submit button not found", screenshots=screenshots)
        close_browser_sync()
        return {"status": "error", "message": "Submit failed", "session_id": session_id}

    except Exception as exc:
        logger.exception("[LINKEDIN_EASY_APPLY] session_id=%s failed", session_id)
        _update_state(session_id, "FAILED", error=str(exc), screenshots=screenshots)
        close_browser_sync()
        return {"status": "error", "message": str(exc), "session_id": session_id}
