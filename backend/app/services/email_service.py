import html
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import resend
from resend.exceptions import ResendError

from app.core.config import settings
from app.models.job import JobDocument

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


def _quality_badge_color(score: int) -> str:
    if score >= 70:
        return "#10b981"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


def _email_shell(inner_content: str, title: str) -> str:
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
                  <td width="48" valign="top">
                    <div style="width:40px;height:40px;border-radius:10px;
                      background:linear-gradient(135deg,#6366f1,#8b5cf6);text-align:center;
                      line-height:40px;font-size:18px;">⚡</div>
                  </td>
                  <td style="padding-left:12px;">
                    <h1 style="margin:0;font-size:22px;font-weight:700;color:#f8fafc;">Career OS</h1>
                    <p style="margin:4px 0 0;font-size:13px;color:#94a3b8;">Your autonomous career assistant</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          {inner_content}
          <tr>
            <td style="padding-top:24px;border-top:1px solid #334155;text-align:center;">
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
        cards.append(
            f"""
            <tr><td style="padding:0 0 16px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
                style="background:#1e293b;border:1px solid #334155;border-radius:12px;">
                <tr><td style="padding:18px 20px;">
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

    text_body = (
        f"{SUBJECT_OPPORTUNITIES}\n\n"
        f"Scan: {scan_label}\nScan ID: {scan_id or 'n/a'}\n\n"
        + "\n".join(text_lines)
        + "\n— Career OS"
    )

    inner = f"""
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

    text_body = (
        f"{SUBJECT_NO_MATCH}\n\n"
        "We scanned engineering opportunities for your profile today, "
        "but no strong matches were found.\n\n"
        "No worries — Career OS will continue searching "
        "for better opportunities automatically.\n\n"
        f"Scan: {scan_label}\n"
        "— Career OS"
    )

    inner = f"""
      <tr><td style="padding:28px 0;">
        <p style="margin:0 0 12px;font-size:16px;font-weight:600;color:#e2e8f0;">
          Daily scan complete
        </p>
        <p style="margin:0 0 16px;font-size:14px;color:#cbd5e1;line-height:1.7;">
          We scanned engineering opportunities for your profile
          <strong style="color:#e2e8f0;">{html.escape(scan_label)}</strong>,
          but no strong matches were found.
        </p>
        <p style="margin:0;font-size:14px;color:#94a3b8;line-height:1.7;">
          No worries — Career OS will continue searching for better
          opportunities automatically 🚀
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
) -> EmailBuildResult:
    """Build email content for preview (opportunities or no-match)."""
    summary = ScanEmailSummary(scan_id=scan_id, scan_timestamp=scan_timestamp)
    if jobs:
        return build_opportunities_email(jobs, summary, recipient_email)
    return build_no_match_email(summary)


def generate_email_preview(
    jobs: list[JobDocument],
    scan_timestamp: str = "",
    scan_id: str = "",
) -> str:
    logger.info("[EMAIL_GENERATION_STARTED] preview jobs=%d", len(jobs))
    built = build_scan_email(jobs, scan_timestamp, scan_id)
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

    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": [recipient],
                "subject": built.subject,
                "html": built.html_body,
                "text": built.text_body,
            }
        )
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
