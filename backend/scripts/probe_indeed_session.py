import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from curl_cffi import requests as cr
from app.automation.browser.session_manager import load_session

storage = load_session("indeed") or {}
for c in storage.get("cookies", [])[:5]:
    print(c.get("domain"), c.get("name"))

cookies = {c["name"]: c["value"] for c in storage.get("cookies", []) if c.get("name")}
for url in [
    "https://in.indeed.com/jobs?q=software+engineer&l=India",
    "https://www.indeed.com/jobs?q=software+engineer&l=India",
]:
    r = cr.get(url, impersonate="chrome120", cookies=cookies, timeout=30)
    print(url, r.status_code, len(r.text), r.text.count("jobTitle"))
