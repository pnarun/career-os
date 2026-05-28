"""Brand asset URLs for API HTML pages, emails, and optional Cloudinary CDN."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Literal

from app.core.config import settings

LogoVariant = Literal["full", "black", "symbol"]

_FILENAMES: dict[LogoVariant, str] = {
    "full": "career-os-logo-full.png",
    "black": "career-os-logo-black.png",
    "symbol": "career-os-logo-symbol.png",
}

_STATIC_BRAND_DIR = Path(__file__).resolve().parent.parent / "static" / "brand"
_CLOUDINARY_FOLDER = "career_os/brand"


def api_brand_logo_url(variant: LogoVariant = "full") -> str:
    """Same-origin path — served from /brand via StaticFiles in main.py."""
    return f"/brand/{_FILENAMES[variant]}"


def _api_public_base() -> str:
    explicit = (getattr(settings, "API_PUBLIC_URL", None) or "").strip().rstrip("/")
    if explicit:
        return explicit
    render_url = (os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
    if render_url:
        return render_url
    return ""


def _env_cdn_url(variant: LogoVariant) -> str:
    mapping = {
        "full": settings.BRAND_LOGO_FULL_URL,
        "black": settings.BRAND_LOGO_BLACK_URL,
        "symbol": settings.BRAND_LOGO_SYMBOL_URL,
    }
    return (mapping.get(variant) or "").strip()


def _is_local_or_untrusted_image_url(url: str) -> bool:
    lower = (url or "").lower()
    return any(
        token in lower
        for token in ("localhost", "127.0.0.1", "0.0.0.0", "192.168.")
    )


def external_brand_logo_url(variant: LogoVariant = "full") -> str:
    """
    Absolute URL for emails and external clients.
    Priority: env CDN (BRAND_LOGO_*_URL) → API /brand → Vercel frontend → local dev.
    Run scripts/upload_brand_logos.py to populate Cloudinary env vars.
    """
    env_url = _env_cdn_url(variant)
    if env_url:
        return env_url

    name = _FILENAMES[variant]
    api_base = _api_public_base()
    if api_base:
        return f"{api_base}/brand/{name}"

    frontend = (settings.FRONTEND_URL or "").strip().rstrip("/")
    if frontend:
        return f"{frontend}/{name}"

    if settings.ENVIRONMENT == "development":
        return f"http://localhost:5173/{name}"

    return ""


def email_brand_logo_url(variant: LogoVariant = "full") -> str:
    """
    Logo URL for transactional email (must be a direct image, not an SPA HTML shell).
    Never uses localhost. Prefers Cloudinary env, then API /brand static route.
    """
    name = _FILENAMES[variant]

    env_url = _env_cdn_url(variant)
    if env_url and not _is_local_or_untrusted_image_url(env_url):
        return env_url

    api_base = _api_public_base()
    if api_base and not _is_local_or_untrusted_image_url(api_base):
        return f"{api_base}/brand/{name}"

    # SPA hosts (e.g. Vercel) may rewrite asset paths to index.html — use API brand route
    render_fallback = (os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
    if render_fallback:
        return f"{render_fallback}/brand/{name}"

    frontend = (settings.FRONTEND_URL or "").strip().rstrip("/")
    if frontend and not _is_local_or_untrusted_image_url(frontend):
        return f"{frontend}/{name}"

    return f"https://career-os-pd9g.onrender.com/brand/{name}"


EMAIL_LOGO_CONTENT_ID = "career-os-logo-full"


def email_logo_inline_attachment() -> dict[str, Any] | None:
    """
    Inline PNG for Resend/Gmail (cid:…) — avoids broken remote URLs on SPA hosts.
    """
    path = _STATIC_BRAND_DIR / _FILENAMES["full"]
    if not path.is_file():
        return None
    return {
        "filename": _FILENAMES["full"],
        "content": base64.b64encode(path.read_bytes()).decode("ascii"),
        "content_id": EMAIL_LOGO_CONTENT_ID,
    }


def email_logo_img_src() -> str:
    """img src for HTML — inline CID when the PNG is bundled on the API."""
    if email_logo_inline_attachment():
        return f"cid:{EMAIL_LOGO_CONTENT_ID}"
    return email_brand_logo_url("full")


def brand_logo_url_for_dark_page(variant: LogoVariant = "full") -> str:
    """Relative URL for API-hosted dark HTML pages."""
    return api_brand_logo_url(variant)
