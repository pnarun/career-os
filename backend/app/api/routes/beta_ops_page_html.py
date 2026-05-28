"""HTML beta operations dashboard (lightweight, no auth — protect in production via network)."""

from __future__ import annotations

import html
import json
from typing import Any


def render_beta_ops_page(
    *,
    app_name: str,
    environment: str,
    logo_url: str,
    favicon_url: str,
    system: dict[str, Any],
    ops: dict[str, Any],
) -> str:
    system_json = html.escape(json.dumps(system, indent=2, default=str))
    ops_json = html.escape(json.dumps(ops, indent=2, default=str))
    from app.api.routes.dev_page_common import (
        dev_page_brand_css,
        dev_page_brand_html,
        dev_page_favicon_link,
    )

    brand = dev_page_brand_html(logo_url)
    favicon = dev_page_favicon_link(favicon_url)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{html.escape(app_name)} — Beta Ops</title>
  {favicon}
  <style>
    :root {{ font-family: system-ui, sans-serif; background: #0f1117; color: #e8eaef; }}
    body {{ margin: 0; padding: 1.5rem; }}
    header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }}
    h1 {{ font-size: 1.25rem; margin: 0; }}
    .env {{ color: #9aa3b5; font-size: 0.875rem; }}
    pre {{
      background: #1a1f2e; border: 1px solid #2a3144; border-radius: 8px;
      padding: 1rem; overflow: auto; font-size: 0.8rem; line-height: 1.45;
    }}
    .grid {{ display: grid; gap: 1rem; }}
    @media (min-width: 900px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
    a {{ color: #8b9cff; }}
    {dev_page_brand_css()}
  </style>
</head>
<body>
  <header>
    {brand}
    <div>
      <h1>Beta operations</h1>
      <p class="env">{html.escape(environment)} · <a href="/health">/health</a> · <a href="/system/metrics">/system/metrics</a></p>
    </div>
  </header>
  <div class="grid">
    <div>
      <h2>System status</h2>
      <pre>{system_json}</pre>
    </div>
    <div>
      <h2>Scan &amp; provider snapshot</h2>
      <pre>{ops_json}</pre>
    </div>
  </div>
</body>
</html>"""
