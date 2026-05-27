"""Ops/admin emails: new signups, deploy notifications (Resend)."""

from __future__ import annotations

import html
import logging
from datetime import datetime, timezone

import resend
from resend.exceptions import ResendError

from app.core.config import settings
from app.services.email_service import EmailNotConfiguredError, EmailServiceError, _configure_resend, _ensure_configured

logger = logging.getLogger(__name__)


def admin_recipient() -> str:
    """Primary ops inbox from env (ADMIN_NOTIFY_EMAIL, else LEGACY_MIGRATION_EMAIL)."""
    return settings.admin_notify_email.strip().lower()


def admin_notify_active() -> bool:
    if not settings.ADMIN_NOTIFY_ENABLED:
        return False
    return bool(admin_recipient())


def _send_admin_message(*, subject: str, text_body: str, html_body: str) -> bool:
    if not admin_notify_active():
        logger.debug("[ADMIN_NOTIFY] skipped (disabled or no ADMIN_NOTIFY_EMAIL)")
        return False

    recipient = admin_recipient()
    try:
        api_key, from_email = _ensure_configured()
    except EmailNotConfiguredError as exc:
        logger.warning("[ADMIN_NOTIFY] not sent: %s", exc)
        return False

    _configure_resend(api_key)
    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": [recipient],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            }
        )
        logger.info("[ADMIN_NOTIFY] sent subject=%s to=%s", subject, recipient)
        return True
    except ResendError as exc:
        logger.error("[ADMIN_NOTIFY] Resend error: %s", exc)
        return False
    except Exception:
        logger.exception("[ADMIN_NOTIFY] send failed")
        return False


def notify_new_user_registration(
    *,
    email: str,
    full_name: str,
    user_id: str,
    timezone: str,
) -> bool:
    """Email ops when a user registers (skipped in development)."""
    if settings.ENVIRONMENT == "development":
        return False
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    name = (full_name or "").strip() or "(not provided)"
    subject = f"Career OS — New user registered: {email}"
    text_body = (
        f"A new user signed up on Career OS.\n\n"
        f"Email: {email}\n"
        f"Name: {name}\n"
        f"User ID: {user_id}\n"
        f"Timezone: {timezone}\n"
        f"Time: {ts}\n"
        f"Environment: {settings.ENVIRONMENT}\n"
    )
    html_body = (
        "<div style='font-family:system-ui,sans-serif;max-width:560px'>"
        "<h2 style='color:#4f46e5'>New Career OS registration</h2>"
        f"<p><strong>Email:</strong> {html.escape(email)}</p>"
        f"<p><strong>Name:</strong> {html.escape(name)}</p>"
        f"<p><strong>User ID:</strong> <code>{html.escape(user_id)}</code></p>"
        f"<p><strong>Timezone:</strong> {html.escape(timezone)}</p>"
        f"<p><strong>Time:</strong> {html.escape(ts)}</p>"
        f"<p><strong>Environment:</strong> {html.escape(settings.ENVIRONMENT)}</p>"
        "</div>"
    )
    return _send_admin_message(subject=subject, text_body=text_body, html_body=html_body)


def notify_deploy_event(
    *,
    component: str,
    status: str = "success",
    url: str = "",
    message: str = "",
) -> bool:
    """Email ops after deploy / CI (Render, Vercel, GitHub)."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    label = component.replace("-", " ").title()
    status_label = status.strip().lower()
    subject = f"Career OS — {label} deploy {status_label}"
    text_body = (
        f"Deploy notification\n\n"
        f"Component: {component}\n"
        f"Status: {status_label}\n"
        f"URL: {url or 'n/a'}\n"
        f"Message: {message or 'n/a'}\n"
        f"Time: {ts}\n"
        f"Environment: {settings.ENVIRONMENT}\n"
    )
    html_body = (
        "<div style='font-family:system-ui,sans-serif;max-width:560px'>"
        f"<h2 style='color:#4f46e5'>{html.escape(label)} — {html.escape(status_label)}</h2>"
        f"<p><strong>URL:</strong> {html.escape(url or 'n/a')}</p>"
        f"<p><strong>Details:</strong> {html.escape(message or 'n/a')}</p>"
        f"<p><strong>Time:</strong> {html.escape(ts)}</p>"
        f"<p><strong>Environment:</strong> {html.escape(settings.ENVIRONMENT)}</p>"
        "</div>"
    )
    return _send_admin_message(subject=subject, text_body=text_body, html_body=html_body)
