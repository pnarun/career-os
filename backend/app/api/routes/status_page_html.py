"""HTML developer hub for API health + UptimeRobot (no iframe — blocked by UptimeRobot)."""

from __future__ import annotations

import html
import json
from typing import Any

from app.api.routes.dev_page_common import (
    dev_page_brand_css,
    dev_page_brand_html,
    dev_page_favicon_link,
)


def _status_badge(status: str) -> str:
    key = (status or "").lower()
    cls = {
        "ok": "ok",
        "running": "ok",
        "disabled": "muted",
        "degraded": "warn",
        "down": "bad",
        "failed": "bad",
        "stopped": "warn",
    }.get(key, "muted")
    return f'<span class="badge {cls}">{html.escape(status)}</span>'


def render_uptime_status_page(
    *,
    status_page_url: str,
    app_name: str,
    environment: str,
    logo_url: str,
    favicon_url: str,
    health: dict[str, Any],
    system: dict[str, Any],
) -> str:
    page_url = html.escape(status_page_url.strip(), quote=True)
    page_label = html.escape(status_page_url.strip())
    logo_html = dev_page_brand_html(logo_url)
    favicon_link = dev_page_favicon_link(favicon_url)

    components = system.get("components") or {}
    component_rows = ""
    for name, data in components.items():
        if not isinstance(data, dict):
            continue
        st = str(data.get("status", "unknown"))
        extra = ""
        if name == "mongodb" and data.get("error"):
            extra = f'<div class="sub">{html.escape(str(data["error"]))}</div>'
        if name == "websocket":
            extra = f'<div class="sub">{data.get("connections", 0)} connection(s)</div>'
        component_rows += (
            f"<tr><td>{html.escape(name)}</td>"
            f"<td>{_status_badge(st)}</td>"
            f"<td>{extra}</td></tr>"
        )

    health_json = html.escape(json.dumps(health, indent=2))
    system_json = html.escape(json.dumps(system, indent=2))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  {favicon_link}
  <title>Career OS — Uptime status</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:#0f172a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; font-size:14px; }}
    header {{
      padding:14px 18px; background:#1e293b; border-bottom:1px solid #334155;
      display:flex; align-items:center; gap:14px; flex-wrap:wrap;
    }}
    {dev_page_brand_css()}
    header h1 {{ margin:0; font-size:18px; }}
    .meta {{ margin:4px 0 0; color:#94a3b8; font-size:12px; }}
    .toolbar {{ display:flex; flex-wrap:wrap; gap:8px; margin-left:auto; }}
    a.btn {{
      display:inline-flex; align-items:center; padding:8px 14px; border-radius:8px;
      background:#4f46e5; color:#fff; text-decoration:none; font-size:13px; font-weight:600;
    }}
    a.btn.secondary {{ background:#334155; font-weight:500; }}
    a.btn:hover {{ filter:brightness(1.08); }}
    main {{ max-width:960px; margin:0 auto; padding:20px 18px 32px; }}
    .card {{
      background:#1e293b; border:1px solid #334155; border-radius:12px;
      padding:18px 20px; margin-bottom:16px;
    }}
    .card h2 {{ margin:0 0 8px; font-size:16px; }}
    .card p {{ margin:0 0 14px; color:#94a3b8; font-size:13px; line-height:1.5; }}
    .hero-cta {{ text-align:center; padding:8px 0 4px; }}
    .hero-cta a.btn {{ font-size:15px; padding:12px 22px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th, td {{ text-align:left; padding:10px 8px; border-bottom:1px solid #334155; }}
    th {{ color:#94a3b8; font-size:11px; text-transform:uppercase; letter-spacing:.04em; }}
    .badge {{
      display:inline-block; padding:2px 10px; border-radius:999px; font-size:11px; font-weight:600;
      text-transform:uppercase;
    }}
    .badge.ok {{ background:#14532d; color:#86efac; }}
    .badge.warn {{ background:#713f12; color:#fcd34d; }}
    .badge.bad {{ background:#7f1d1d; color:#fca5a5; }}
    .badge.muted {{ background:#334155; color:#cbd5e1; }}
    .sub {{ font-size:12px; color:#64748b; margin-top:4px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin-top:12px; }}
    .stat {{ background:#0f172a; border-radius:8px; padding:12px; border:1px solid #334155; }}
    .stat label {{ display:block; font-size:11px; color:#94a3b8; text-transform:uppercase; }}
    .stat strong {{ font-size:18px; }}
    pre {{
      margin:12px 0 0; padding:12px; background:#0f172a; border-radius:8px;
      overflow:auto; font-size:11px; line-height:1.45; color:#cbd5e1; max-height:200px;
    }}
    .note {{
      font-size:12px; color:#94a3b8; border-left:3px solid #6366f1; padding-left:10px; margin-top:10px;
    }}
  </style>
</head>
<body>
  <header>
    {logo_html}
    <div>
      <h1>Uptime &amp; service status</h1>
      <p class="meta">{html.escape(app_name)} · {html.escape(environment)}</p>
    </div>
    <nav class="toolbar" aria-label="Developer links">
      <a class="btn secondary" href="/health">Health JSON</a>
      <a class="btn secondary" href="/system/status">System JSON</a>
      <a class="btn secondary" href="/logs">Logs</a>
      <a class="btn" href="/uptime/go">UptimeRobot dashboard ↗</a>
    </nav>
  </header>
  <main>
    <section class="card">
      <h2>UptimeRobot public status</h2>
      <p>
        UptimeRobot does not allow embedding their status page in an iframe
        (<code>refused to connect</code>). Open the full dashboard in a new tab instead.
      </p>
      <div class="hero-cta">
        <a class="btn" href="/uptime/go" target="_blank" rel="noopener noreferrer">
          Open {page_label} ↗
        </a>
      </div>
      <p class="note">Shortcut: <code>GET /uptime/go</code> redirects to your configured status page.</p>
    </section>

    <section class="card">
      <h2>API health (this server)</h2>
      <div class="grid">
        <div class="stat">
          <label>Health</label>
          <strong>{_status_badge(str(health.get("status", "ok")))}</strong>
        </div>
        <div class="stat">
          <label>Scheduler</label>
          <strong>{_status_badge(str(health.get("scheduler", "unknown")))}</strong>
        </div>
        <div class="stat">
          <label>Overall</label>
          <strong>{_status_badge(str(system.get("status", "unknown")))}</strong>
        </div>
      </div>
      <table style="margin-top:16px">
        <thead><tr><th>Component</th><th>Status</th><th>Details</th></tr></thead>
        <tbody>{component_rows or '<tr><td colspan="3" class="sub">No component data</td></tr>'}</tbody>
      </table>
      <details style="margin-top:14px">
        <summary style="cursor:pointer;color:#a5b4fc">Raw JSON</summary>
        <pre>{health_json}</pre>
        <pre>{system_json}</pre>
      </details>
    </section>
  </main>
</body>
</html>"""
