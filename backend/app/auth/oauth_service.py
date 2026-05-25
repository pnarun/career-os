"""
Google OAuth extension point (MVP stub).

Configure when ready:
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  GOOGLE_OAUTH_REDIRECT_URI
"""

from app.core.config import settings


def google_oauth_enabled() -> bool:
    return bool(
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
        and settings.GOOGLE_OAUTH_REDIRECT_URI
    )


def get_google_authorize_url() -> str | None:
    if not google_oauth_enabled():
        return None
    # Placeholder for Phase 11+ OAuth flow
    return None
