"""Detect application form types and field structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DetectedField:
    label: str
    field_type: str
    selector_hint: str = ""
    required: bool = False


@dataclass
class FormDetectionResult:
    apply_type: str = "unknown"
    is_easy_apply: bool = False
    is_multi_step: bool = False
    fields: list[DetectedField] = field(default_factory=list)
    has_resume_upload: bool = False
    has_captcha: bool = False
    error: str = ""


LINKEDIN_EASY_APPLY_SELECTORS = (
    "#jobs-apply-button-id",
    "button.jobs-apply-button",
    "button.jobs-s-apply",
    ".jobs-s-apply button",
    "button[aria-label*='Easy Apply']",
    "button[aria-label*='easy apply']",
    ".jobs-apply-button--top-card",
    ".jobs-apply-button",
)

LINKEDIN_MODAL_SELECTORS = (
    ".jobs-easy-apply-modal",
    "div[role='dialog']",
    "div.artdeco-modal",
)

FIELD_LABEL_SELECTORS = (
    "label",
    "legend",
    "span.t-14",
    "h3",
)


def detect_linkedin_apply_type(page: Any) -> FormDetectionResult:
    """Detect LinkedIn Easy Apply vs external apply."""
    result = FormDetectionResult()

    for selector in LINKEDIN_EASY_APPLY_SELECTORS:
        try:
            loc = page.locator(selector)
            if loc.count() == 0:
                continue
            for i in range(min(loc.count(), 3)):
                btn = loc.nth(i)
                if not btn.is_visible():
                    continue
                text = (btn.inner_text(timeout=2000) or "").lower()
                aria = (btn.get_attribute("aria-label") or "").lower()
                if "easy apply" in text or "easy apply" in aria:
                    result.is_easy_apply = True
                    result.apply_type = "linkedin_easy_apply"
                    return result
        except Exception:
            continue

    try:
        role_btn = page.get_by_role("button", name="Easy Apply")
        if role_btn.count() > 0 and role_btn.first.is_visible():
            result.is_easy_apply = True
            result.apply_type = "linkedin_easy_apply"
            return result
    except Exception:
        pass

    try:
        body = (page.locator("body").inner_text(timeout=3000) or "").lower()
        if "easy apply" in body:
            result.is_easy_apply = True
            result.apply_type = "linkedin_easy_apply"
        elif "apply" in body:
            result.apply_type = "external_apply"
    except Exception:
        result.error = "Could not detect apply type"

    return result


def detect_form_fields(page: Any, *, container_selector: str = "") -> list[DetectedField]:
    """Detect visible form fields within optional container."""
    fields: list[DetectedField] = []
    root = page.locator(container_selector) if container_selector else page

    try:
        inputs = root.locator("input:visible, select:visible, textarea:visible")
        count = min(inputs.count(), 30)
    except Exception:
        return fields

    for i in range(count):
        try:
            el = inputs.nth(i)
            input_type = el.get_attribute("type") or "text"
            if input_type in ("hidden", "submit", "button"):
                continue

            label = _resolve_field_label(el, page)
            field_type = _classify_field(label, input_type)
            fields.append(
                DetectedField(
                    label=label or f"field_{i}",
                    field_type=field_type,
                    required=el.get_attribute("required") is not None,
                )
            )
        except Exception:
            continue

    return fields


def detect_resume_upload(page: Any, *, container_selector: str = "") -> bool:
    root = page.locator(container_selector) if container_selector else page
    try:
        return root.locator("input[type='file']").count() > 0
    except Exception:
        return False


def _resolve_field_label(element: Any, page: Any) -> str:
    for attr in ("aria-label", "placeholder", "name", "id"):
        try:
            value = element.get_attribute(attr)
            if value and value.strip():
                return value.strip()
        except Exception:
            pass
    return ""


def _classify_field(label: str, input_type: str) -> str:
    text = label.lower()
    if input_type == "file":
        return "resume_upload"
    if any(k in text for k in ("email", "e-mail")):
        return "email"
    if any(k in text for k in ("phone", "mobile", "contact")):
        return "phone"
    if any(k in text for k in ("salary", "compensation", "ctc")):
        return "salary"
    if any(k in text for k in ("notice", "availability")):
        return "notice_period"
    if any(k in text for k in ("visa", "sponsor", "authorization", "work permit")):
        return "work_authorization"
    if any(k in text for k in ("relocate", "relocation", "willing to move")):
        return "relocation"
    if any(k in text for k in ("year", "experience")):
        return "years_of_experience"
    if input_type in ("checkbox", "radio"):
        return "choice"
    if input_type == "select-one":
        return "dropdown"
    return "text"
