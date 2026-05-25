import json
import re
from curl_cffi import requests as cr

html = cr.get(
    "https://in.indeed.com/jobs?q=software+engineer&l=India",
    impersonate="chrome120",
    timeout=30,
).text
print("len", len(html), "jobTitle count", html.count("jobTitle"))

jks = re.findall(r'"jobKey":"([a-f0-9]+)"', html)
print("jobKeys", len(jks), jks[:3])

titles = re.findall(r'"jobTitle":"((?:\\.|[^"\\])*)"', html)
print("titles", len(titles), [json.loads(f'"{t}"') for t in titles[:3]])

subs = re.findall(r'"subtitle":"((?:\\.|[^"\\])*)"', html)
print("subs", len(subs), [json.loads(f'"{s}"') for s in subs[:3]])

# build apply urls
for jk, title, sub in zip(jks[:5], titles[:5], subs[:5]):
    title = json.loads(f'"{title}"')
    sub = json.loads(f'"{sub}"')
    url = f"https://in.indeed.com/viewjob?jk={jk}"
    company = sub.split(" - ")[0].strip() if " - " in sub else sub
    print("job", title, company, url)
