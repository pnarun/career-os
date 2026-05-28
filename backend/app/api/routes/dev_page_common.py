"""Shared HTML fragments for API dev pages (/logs, /uptime) — dark theme."""

from __future__ import annotations

import html


def dev_page_favicon_link(favicon_url: str) -> str:
    if not favicon_url:
        return ""
    return f'<link rel="icon" type="image/png" href="{html.escape(favicon_url)}"/>'


def dev_page_brand_css() -> str:
    """Logo on dark header — no white pill (full wordmark has light text)."""
    return """
    header .brand { display:flex; align-items:center; flex-shrink:0; }
    header .brand img {
      height: 38px; width: auto; max-width: 220px;
      object-fit: contain; object-position: left center;
      display: block;
    }
    """


def dev_page_brand_html(logo_url: str, *, alt: str = "Career OS") -> str:
    if not logo_url:
        return ""
    return (
        f'<div class="brand">'
        f'<img src="{html.escape(logo_url)}" alt="{html.escape(alt)}" />'
        f"</div>"
    )
