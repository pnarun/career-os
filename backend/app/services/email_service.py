import html
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import resend
from resend.exceptions import ResendError

from app.core.config import settings
from app.models.job import JobDocument
from app.models.scan_session import ScanSummaryDetail

logger = logging.getLogger(__name__)

EMAIL_JOB_LIMIT = 15
SUBJECT_OPPORTUNITIES = "Career OS — Opportunities Found 🚀"
SUBJECT_NO_MATCH = "Career OS — Daily Scan Complete"


class EmailServiceError(Exception):
    """Raised when email delivery fails."""


class EmailNotConfiguredError(EmailServiceError):
    """Raised when Resend credentials are missing."""


@dataclass
class ScanEmailSummary:
    scan_id: str = ""
    scan_timestamp: str = ""
    analytics: ScanSummaryDetail | None = None


@dataclass
class EmailBuildResult:
    subject: str
    text_body: str
    html_body: str
    jobs_included: int
    email_type: str  # opportunities | no_match


@dataclass
class EmailSendResult:
    sent: bool
    jobs_sent: int
    email_to: str
    email_type: str
    sent_at: str = ""
    error: str = ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_configured() -> tuple[str, str]:
    api_key = (settings.RESEND_API_KEY or "").strip()
    from_email = (settings.RESEND_FROM_EMAIL or "").strip()
    if not from_email:
        from_email = "Career OS <onboarding@resend.dev>"
    if not api_key:
        raise EmailNotConfiguredError(
            "Resend is not configured. Set RESEND_API_KEY and RESEND_FROM_EMAIL."
        )
    return api_key, from_email


def _configure_resend(api_key: str) -> None:
    resend.api_key = api_key


def _format_missing_skills(skills: list[str]) -> str:
    if not skills:
        return "None listed"
    visible = skills[:5]
    suffix = f" +{len(skills) - 5} more" if len(skills) > 5 else ""
    return ", ".join(visible) + suffix


def _match_badge_color(match_pct: int) -> str:
    if match_pct >= 75:
        return "#22c55e"
    if match_pct >= 50:
        return "#3b82f6"
    if match_pct >= 30:
        return "#f59e0b"
    return "#94a3b8"


def _format_source_label(source_key: str) -> str:
    labels = {
        "remoteok": "RemoteOK",
        "arbeitnow": "Arbeitnow",
        "indeed": "Indeed",
        "naukri": "Naukri",
        "instahyre": "Instahyre",
        "linkedin": "LinkedIn",
    }
    return labels.get((source_key or "").lower(), source_key.title() or "Unknown")


def _build_email_analytics_html(analytics: ScanSummaryDetail | None) -> str:
    if not analytics:
        return ""

    platform_rows = []
    for source_key, count in sorted(
        analytics.sources.items(),
        key=lambda item: -item[1],
    ):
        if count <= 0 and source_key not in analytics.failed_sources:
            continue
        label = _format_source_label(source_key)
        platform_rows.append(
            f"<li style='margin:4px 0;color:#cbd5e1;'>{html.escape(label)}: "
            f"<strong style='color:#e2e8f0;'>{count}</strong></li>"
        )

    listed_failures: set[str] = set()
    for item in analytics.provider_status or []:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "success":
            continue
        source_key = str(item.get("source", ""))
        listed_failures.add(source_key)
        label = _format_source_label(source_key)
        error_type = html.escape(str(item.get("error_type", "unknown")))
        error_message = html.escape(str(item.get("error_message", "Fetch failed")))
        platform_rows.append(
            f"<li style='margin:4px 0;color:#fbbf24;'>{html.escape(label)}: "
            f"<span>{error_type} — {error_message}</span></li>"
        )

    for failed in analytics.failed_sources:
        if failed in listed_failures:
            continue
        if failed not in analytics.sources or analytics.sources.get(failed, 0) <= 0:
            label = _format_source_label(failed)
            detail = html.escape("Fetch failed (no diagnostic recorded)")
            platform_rows.append(
                f"<li style='margin:4px 0;color:#fbbf24;'>{html.escape(label)}: "
                f"<span>{detail}</span></li>"
            )

    platforms_html = "".join(platform_rows) or (
        "<li style='color:#94a3b8;'>No platform data for this scan</li>"
    )

    qualified_line = (
        f"<p style='margin:12px 0 0;font-size:14px;color:#a5b4fc;font-weight:600;'>"
        f"Qualified matches found: {analytics.qualified_jobs}</p>"
        if analytics.qualified_jobs > 0
        else ""
    )

    return f"""
      <tr><td style="padding:0 0 20px;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
          style="background:#1e293b;border:1px solid #334155;border-radius:12px;">
          <tr><td style="padding:20px;">
            <p style="margin:0 0 6px;font-size:18px;font-weight:700;color:#f8fafc;">
              Career Lens Daily Scan Summary
            </p>
            <p style="margin:0;font-size:14px;color:#94a3b8;line-height:1.6;">
              Scanned <strong style="color:#e2e8f0;">{analytics.total_fetched}</strong>
              jobs across <strong style="color:#e2e8f0;">{analytics.platforms_scanned}</strong>
              platforms.
            </p>
            <p style="margin:14px 0 6px;font-size:13px;font-weight:600;color:#cbd5e1;">
              Platforms scanned:
            </p>
            <ul style="margin:0;padding-left:18px;font-size:13px;">
              {platforms_html}
            </ul>
            {qualified_line}
          </td></tr>
        </table>
      </td></tr>
    """


def _quality_badge_color(score: int) -> str:
    if score >= 70:
        return "#10b981"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


def _portal_url() -> str:
    url = (settings.FRONTEND_URL or "").strip().rstrip("/")
    if url:
        return url
    return "https://career-os-two-chi.vercel.app"


def _logo_img_src() -> str:
    from app.core.brand_assets import email_logo_img_src

    return email_logo_img_src()


def _email_logo_attachments() -> list[dict]:
    from app.core.brand_assets import email_logo_inline_attachment

    attachment = email_logo_inline_attachment()
    return [attachment] if attachment else []


def _email_footer_plain() -> str:
    return (
        f"\n\nOpen Career OS: {_portal_url()}\n\n"
        "This email is not monitored. Please do not reply to this email.\n"
        "— Career OS"
    )


def _build_portal_cta_html() -> str:
    url = html.escape(_portal_url())
    return f"""
          <tr>
            <td style="padding:28px 0 8px;text-align:center;">
              <a href="{url}" style="display:inline-block;padding:12px 28px;
                background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#ffffff;
                text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;">
                Open Career OS portal
              </a>
              <p style="margin:10px 0 0;font-size:12px;color:#64748b;line-height:1.5;">
                Sign in to view all matches, track applications, and manage your scans
              </p>
            </td>
          </tr>
    """


def _email_shell(inner_content: str, title: str) -> str:
    portal_cta = _build_portal_cta_html()
    logo_src = _logo_img_src()
    if not logo_src.startswith("cid:"):
        logo_src = html.escape(logo_src)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{html.escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#0f172a;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:640px;">
          <tr>
            <td style="padding-bottom:24px;border-bottom:1px solid #334155;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td width="56" valign="middle">
                    <img src="{logo_url}" alt="Career OS" width="180" height="48"
                      style="display:block;height:48px;width:auto;max-width:200px;" />
                  </td>
                  <td style="padding-left:12px;" valign="middle">
                    <h1 style="margin:0;font-size:22px;font-weight:700;color:#f8fafc;">Career OS</h1>
                    <p style="margin:4px 0 0;font-size:13px;color:#94a3b8;">Your autonomous career assistant</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          {inner_content}
          {portal_cta}
          <tr>
            <td style="padding-top:20px;border-top:1px solid #334155;text-align:center;">
              <p style="margin:0 0 8px;font-size:11px;color:#64748b;line-height:1.6;">
                This email is not monitored. Please do not reply to this email.
              </p>
              <p style="margin:0;font-size:11px;color:#475569;line-height:1.6;">
                Career OS · Intelligent job discovery &amp; matching
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_job_cards_html(jobs: list[JobDocument]) -> str:
    cards: list[str] = []
    for index, job in enumerate(jobs[:EMAIL_JOB_LIMIT], start=1):
        location = job.location or "Remote"
        missing = _format_missing_skills(job.missing_skills)
        apply_url = html.escape(job.apply_url or "")
        match_color = _match_badge_color(job.match_percentage)
        quality_color = _quality_badge_color(job.job_quality_score)
        apply_block = (
            f'<a href="{apply_url}" style="display:inline-block;margin-top:12px;padding:10px 18px;'
            f'background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#ffffff;text-decoration:none;'
            f'border-radius:8px;font-size:13px;font-weight:600;">Apply Now</a>'
            if apply_url and job.has_apply_url and not job.is_suspicious
            else '<span style="color:#64748b;font-size:12px;">Apply link unavailable</span>'
        )
        source_label = _format_source_label(job.source or "")
        cards.append(
            f"""
            <tr><td style="padding:0 0 16px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                style="background:#1e293b;border:1px solid #334155;border-radius:12px;">
                <tr><td style="padding:18px 20px;">
                  <span style="display:inline-block;margin-bottom:8px;padding:3px 10px;
                    border-radius:999px;font-size:11px;font-weight:600;
                    background:#312e81;color:#c7d2fe;">Source: {html.escape(source_label)}</span>
                  <span style="color:#64748b;font-size:11px;font-weight:600;">#{index}</span>
                  <h3 style="margin:6px 0 4px;font-size:17px;font-weight:600;color:#f8fafc;">
                    {html.escape(job.title)}
                  </h3>
                  <p style="margin:0;font-size:14px;color:#94a3b8;">{html.escape(job.company)}</p>
                  <p style="margin:12px 0 6px;font-size:13px;color:#cbd5e1;">
                    <strong style="color:#e2e8f0;">Match:</strong>
                    <span style="color:{match_color};font-weight:700;">{job.match_percentage}%</span>
                    &nbsp;·&nbsp;
                    <strong style="color:#e2e8f0;">Quality:</strong>
                    <span style="color:{quality_color};font-weight:600;">{job.job_quality_score}/100</span>
                  </p>
                  <p style="margin:0 0 6px;font-size:13px;color:#cbd5e1;">
                    <strong style="color:#e2e8f0;">Location:</strong> {html.escape(location)}
                  </p>
                  <p style="margin:0;font-size:12px;color:#94a3b8;">
                    <strong style="color:#cbd5e1;">Missing skills:</strong> {html.escape(missing)}
                  </p>
                  {apply_block}
                </td></tr>
              </table>
            </td></tr>
            """
        )
    return "".join(cards)


def build_opportunities_email(
    jobs: list[JobDocument],
    scan_summary: ScanEmailSummary,
    recipient_email: str = "",
) -> EmailBuildResult:
    top_jobs = jobs[:EMAIL_JOB_LIMIT]
    extra_count = max(0, len(jobs) - len(top_jobs))
    scan_label = scan_summary.scan_timestamp or "Latest scan"
    scan_id = scan_summary.scan_id

    text_lines = []
    for index, job in enumerate(top_jobs, start=1):
        text_lines.append(
            f"{index}. {job.title} @ {job.company}\n"
            f"   Match: {job.match_percentage}% | Quality: {job.job_quality_score}\n"
            f"   Location: {job.location or 'Remote'}\n"
            f"   Missing: {_format_missing_skills(job.missing_skills)}\n"
            f"   Apply: {job.apply_url or 'N/A'}\n"
        )

    overflow_line = ""
    if extra_count > 0:
        overflow_line = (
            f"\n\n{extra_count} more job{'s' if extra_count != 1 else ''} "
            "are waiting for you on Career OS — open the Jobs feed to review them all."
        )

    text_body = (
        f"{SUBJECT_OPPORTUNITIES}\n\n"
        f"Scan: {scan_label}\nScan ID: {scan_id or 'n/a'}\n\n"
        + "\n".join(text_lines)
        + overflow_line
        + _email_footer_plain()
    )

    analytics_block = _build_email_analytics_html(scan_summary.analytics)

    inner = f"""
      {analytics_block}
      <tr><td style="padding:20px 0 8px;">
        <p style="margin:0 0 4px;font-size:16px;font-weight:600;color:#e2e8f0;">
          Curated opportunities for you
        </p>
        <p style="margin:0;font-size:13px;color:#64748b;">
          Scan completed · {html.escape(scan_label)}
          {f' · {html.escape(scan_id)}' if scan_id else ''}
        </p>
        <p style="margin:8px 0 0;font-size:12px;color:#475569;">
          Top {len(top_jobs)} matches · delivered to {html.escape(recipient_email or 'you')}
        </p>
        {f'<p style="margin:10px 0 0;font-size:13px;color:#fbbf24;">{extra_count} more job{"s" if extra_count != 1 else ""} are waiting for your glance on Career OS — visit the Jobs feed to see them all.</p>' if extra_count > 0 else ''}
      </td></tr>
      <tr><td>
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
          {_build_job_cards_html(top_jobs)}
        </table>
      </td></tr>
    """

    return EmailBuildResult(
        subject=SUBJECT_OPPORTUNITIES,
        text_body=text_body,
        html_body=_email_shell(inner, SUBJECT_OPPORTUNITIES),
        jobs_included=len(top_jobs),
        email_type="opportunities",
    )


def build_no_match_email(scan_summary: ScanEmailSummary) -> EmailBuildResult:
    scan_label = scan_summary.scan_timestamp or "today"
    analytics = scan_summary.analytics

    platform_text = ""
    if analytics:
        lines = [
            f"- {_format_source_label(k)}: {v}"
            for k, v in sorted(analytics.sources.items(), key=lambda x: -x[1])
            if v > 0
        ]
        for item in analytics.provider_status or []:
            if not isinstance(item, dict) or item.get("status") == "success":
                continue
            label = _format_source_label(str(item.get("source", "")))
            err = item.get("error_type", "unknown")
            msg = item.get("error_message", "")
            lines.append(f"- {label}: {err} — {msg}")
        for failed in analytics.failed_sources:
            if any(
                isinstance(p, dict) and p.get("source") == failed
                for p in (analytics.provider_status or [])
            ):
                continue
            lines.append(f"- {_format_source_label(failed)}: fetch failed")
        platform_text = "\n".join(lines)

    text_body = (
        f"{SUBJECT_NO_MATCH}\n\n"
        "Career OS Daily Scan Summary\n\n"
        f"{platform_text}\n\n"
        "No strong matches were found today, but Career OS continues scanning "
        "opportunities intelligently for you.\n\n"
        f"Scan: {scan_label}"
        + _email_footer_plain()
    )

    analytics_block = _build_email_analytics_html(analytics)

    inner = f"""
      {analytics_block}
      <tr><td style="padding:8px 0 24px;">
        <p style="margin:0;font-size:14px;color:#cbd5e1;line-height:1.75;">
          No strong matches were found today, but Career Lens continues scanning
          India and remote engineering opportunities intelligently for you 🚀
        </p>
      </td></tr>
    """

    return EmailBuildResult(
        subject=SUBJECT_NO_MATCH,
        text_body=text_body,
        html_body=_email_shell(inner, SUBJECT_NO_MATCH),
        jobs_included=0,
        email_type="no_match",
    )


def build_scan_email(
    jobs: list[JobDocument],
    scan_timestamp: str = "",
    scan_id: str = "",
    recipient_email: str = "",
    analytics: ScanSummaryDetail | None = None,
) -> EmailBuildResult:
    """Build email content for preview (opportunities or no-match)."""
    summary = ScanEmailSummary(
        scan_id=scan_id,
        scan_timestamp=scan_timestamp,
        analytics=analytics,
    )
    if jobs:
        return build_opportunities_email(jobs, summary, recipient_email)
    return build_no_match_email(summary)


def generate_email_preview(
    jobs: list[JobDocument],
    scan_timestamp: str = "",
    scan_id: str = "",
    analytics: ScanSummaryDetail | None = None,
) -> str:
    logger.info("[EMAIL_GENERATION_STARTED] preview jobs=%d", len(jobs))
    built = build_scan_email(jobs, scan_timestamp, scan_id, analytics=analytics)
    logger.info(
        "[EMAIL_PREVIEW_GENERATED] type=%s jobs=%d",
        built.email_type,
        built.jobs_included,
    )
    return built.html_body


def _dispatch_resend(
    to_email: str,
    built: EmailBuildResult,
) -> EmailSendResult:
    api_key, from_email = _ensure_configured()
    recipient = to_email.strip()
    if not recipient:
        raise EmailServiceError("Recipient email is required")

    logger.info(
        "[EMAIL_GENERATION_STARTED] type=%s to=%s jobs=%d",
        built.email_type,
        recipient,
        built.jobs_included,
    )

    _configure_resend(api_key)

    payload: dict = {
        "from": from_email,
        "to": [recipient],
        "subject": built.subject,
        "html": built.html_body,
        "text": built.text_body,
    }
    attachments = _email_logo_attachments()
    if attachments:
        payload["attachments"] = attachments

    try:
        resend.Emails.send(payload)
        sent_at = _utc_now_iso()
        if built.email_type == "no_match":
            logger.info("[NO_MATCH_EMAIL_SENT] to=%s", recipient)
        else:
            logger.info(
                "[EMAIL_SENT_SUCCESS] to=%s jobs=%d",
                recipient,
                built.jobs_included,
            )
        return EmailSendResult(
            sent=True,
            jobs_sent=built.jobs_included,
            email_to=recipient,
            email_type=built.email_type,
            sent_at=sent_at,
        )
    except ResendError as exc:
        message = str(exc).strip() or "Resend rejected the email request."
        logger.error("[EMAIL_SENT_FAILURE] to=%s resend_error=%s", recipient, message)
        raise EmailServiceError(message) from exc
    except Exception as exc:
        logger.exception("[EMAIL_SENT_FAILURE] to=%s", recipient)
        raise EmailServiceError(f"Failed to send email via Resend: {exc}") from exc


def send_password_reset_otp(email: str, otp: str) -> None:
    """Send a 6-digit password reset code."""
    recipient = email.strip().lower()
    subject = "Career OS — Password reset code"
    text_body = (
        f"Your Career OS password reset code is: {otp}\n\n"
        "This code expires in 10 minutes. If you did not request this, ignore this email."
    )
    html_body = _email_shell(
        f"""
          <tr><td style="padding:24px 0;">
            <p style="margin:0 0 12px;font-size:15px;color:#e2e8f0;">
              Your Career OS password reset code is:
            </p>
            <p style="margin:0 0 16px;font-size:28px;font-weight:700;letter-spacing:4px;color:#f8fafc;">
              {html.escape(otp)}
            </p>
            <p style="margin:0;font-size:14px;color:#94a3b8;line-height:1.6;">
              This code expires in 10 minutes. If you did not request this, you can ignore this email.
            </p>
          </td></tr>
        """,
        subject,
    )
    api_key, from_email = _ensure_configured()
    _configure_resend(api_key)
    payload: dict = {
        "from": from_email,
        "to": [recipient],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    attachments = _email_logo_attachments()
    if attachments:
        payload["attachments"] = attachments

    try:
        resend.Emails.send(payload)
        logger.info("[PASSWORD_RESET_OTP_SENT] to=%s", recipient)
    except ResendError as exc:
        raise EmailServiceError(str(exc)) from exc


def send_scan_results_email(
    email: str,
    jobs: list[JobDocument],
    scan_summary: ScanEmailSummary | None = None,
) -> EmailSendResult:
    """
    Send curated opportunities or supportive no-match email via Resend SDK.
    Always attempts delivery (one email per call).
    """
    logger.info("[EMAIL_SEND_REQUESTED] to=%s jobs=%d", email, len(jobs))
    summary = scan_summary or ScanEmailSummary()

    if jobs:
        built = build_opportunities_email(jobs, summary, email)
    else:
        built = build_no_match_email(summary)

    return _dispatch_resend(email, built)
