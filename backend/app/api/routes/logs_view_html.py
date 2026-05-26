"""HTML template for /logs table viewer."""

from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote


def render_logs_page(
    *,
    entries: list[dict[str, Any]],
    users: list[str],
    limit: int,
    user_filter: str,
    level_filter: str,
    app_name: str,
    environment: str,
) -> str:
    rows_html = ""
    for e in entries:
        level = e.get("level", "INFO")
        level_cls = {
            "ERROR": "lvl-error",
            "WARNING": "lvl-warn",
            "INFO": "lvl-info",
            "DEBUG": "lvl-debug",
        }.get(level, "lvl-info")
        rows_html += (
            f"<tr data-user=\"{html.escape(e.get('user', ''))}\" data-level=\"{html.escape(level)}\">"
            f"<td class=\"ts\">{html.escape(e.get('timestamp_human', ''))}</td>"
            f"<td class=\"user\">{html.escape(e.get('user', ''))}</td>"
            f"<td class=\"log\"><span class=\"{level_cls}\">[{html.escape(level)}]</span> "
            f"{html.escape(e.get('message', ''))}</td></tr>\n"
        )

    if not rows_html:
        rows_html = '<tr><td colspan="3" class="empty">No logs yet — trigger API traffic or run a scan.</td></tr>'

    user_options = '<option value="">All users</option>'
    for u in users:
        sel = " selected" if u == user_filter else ""
        user_options += f'<option value="{html.escape(u)}"{sel}>{html.escape(u)}</option>'

    level_options = '<option value="">All levels</option>'
    for lvl in ("ERROR", "WARNING", "INFO", "DEBUG"):
        sel = " selected" if lvl == level_filter else ""
        level_options += f'<option value="{lvl}"{sel}>{lvl}</option>'

    export_qs = f"limit={limit}"
    if user_filter:
        export_qs += f"&user={quote(user_filter)}"
    if level_filter:
        export_qs += f"&level={quote(level_filter)}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Career OS — Logs</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:#0f172a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; font-size:13px; }}
    header {{ padding:14px 18px; background:#1e293b; border-bottom:1px solid #334155; }}
    header h1 {{ margin:0 0 6px; font-size:18px; }}
    .meta {{ color:#94a3b8; font-size:12px; }}
    .toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; padding:12px 18px; background:#1e293b; border-bottom:1px solid #334155; }}
    .toolbar label {{ font-size:12px; color:#94a3b8; display:flex; flex-direction:column; gap:4px; }}
    select, input[type=search] {{ background:#0f172a; border:1px solid #475569; color:#e2e8f0; border-radius:6px; padding:6px 10px; min-width:140px; }}
    a.btn, button.btn {{ display:inline-flex; align-items:center; padding:7px 12px; border-radius:6px; background:#4f46e5; color:#fff; text-decoration:none; border:none; cursor:pointer; font-size:12px; }}
    a.btn.secondary {{ background:#334155; }}
    table {{ width:100%; border-collapse:collapse; }}
    th {{ text-align:left; padding:10px 14px; background:#1e293b; color:#94a3b8; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.04em; position:sticky; top:0; }}
    td {{ padding:10px 14px; border-bottom:1px solid #1e293b; vertical-align:top; }}
    td.ts {{ white-space:nowrap; color:#94a3b8; font-family:ui-monospace,monospace; font-size:11px; width:180px; }}
    td.user {{ white-space:nowrap; color:#a5b4fc; width:200px; }}
    td.log {{ font-family:ui-monospace,monospace; font-size:12px; line-height:1.45; word-break:break-word; }}
    .lvl-error {{ color:#f87171; }}
    .lvl-warn {{ color:#fbbf24; }}
    .lvl-info {{ color:#94a3b8; }}
    .lvl-debug {{ color:#64748b; }}
    .empty {{ text-align:center; color:#64748b; padding:32px; }}
    .wrap {{ overflow-x:auto; max-height:calc(100vh - 200px); }}
    @media (max-width:640px) {{
      td.user {{ display:none; }}
      th:nth-child(2) {{ display:none; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Career OS API Logs</h1>
    <p class="meta">{html.escape(app_name)} · {html.escape(environment)} · {len(entries)} rows · refreshes every 10s</p>
  </header>
  <form class="toolbar" method="get" action="/logs">
    <label>Lines
      <select name="limit">
        <option value="100"{" selected" if limit == 100 else ""}>100</option>
        <option value="200"{" selected" if limit == 200 else ""}>200</option>
        <option value="500"{" selected" if limit == 500 else ""}>500</option>
      </select>
    </label>
    <label>User
      <select name="user">{user_options}</select>
    </label>
    <label>Level
      <select name="level">{level_options}</select>
    </label>
    <label>Search log text
      <input type="search" id="q" placeholder="Filter in browser…"/>
    </label>
    <button type="submit" class="btn">Apply</button>
    <a class="btn secondary" href="/logs/export?{export_qs}">Export CSV (Excel)</a>
    <a class="btn secondary" href="/logs/api?limit={limit}">JSON API</a>
    <a class="btn secondary" href="/health">Health</a>
    <a class="btn secondary" href="/docs">Docs</a>
  </form>
  <div class="wrap">
    <table id="log-table">
      <thead>
        <tr><th>Timestamp (UTC)</th><th>User</th><th>Log</th></tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <script>
    const q = document.getElementById('q');
    q?.addEventListener('input', () => {{
      const needle = q.value.toLowerCase();
      document.querySelectorAll('#log-table tbody tr').forEach((row) => {{
        const text = row.textContent.toLowerCase();
        row.style.display = !needle || text.includes(needle) ? '' : 'none';
      }});
    }});
    setTimeout(() => location.reload(), 10000);
  </script>
</body>
</html>"""
