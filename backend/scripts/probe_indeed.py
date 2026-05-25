import requests

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://in.indeed.com/",
}

session = requests.Session()
session.headers.update(UA)
web = "https://in.indeed.com/jobs?q=software+engineer&l=India"
rss = "https://in.indeed.com/rss?q=software+engineer&l=India&sort=date"

for label, url, accept in [
    ("web", web, UA["Accept"]),
    ("rss", rss, "application/rss+xml, application/xml, text/xml, */*"),
]:
    r = session.get(url, headers={"Accept": accept}, timeout=30)
    print(label, r.status_code, len(r.text))
    if r.status_code == 200:
        print("  items", r.text.count("<item>"), "jobTitle", r.text.count("jobTitle"))
