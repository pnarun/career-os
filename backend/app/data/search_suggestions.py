"""Search suggestions for roles, skills, and target companies."""

from __future__ import annotations

from app.utils.skills_master import SKILLS_MASTER

ROLE_SUFFIXES = (
    "Developer",
    "Engineer",
    "Consultant",
    "Architect",
    "Lead",
    "Senior Developer",
    "Senior Engineer",
)

ROLE_SEEDS = (
    "Angular",
    "React",
    "Full Stack",
    "Backend",
    "Frontend",
    "Python",
    "Java",
    "Node.js",
    "DevOps",
    "Cloud",
    "Data Engineer",
    "Machine Learning",
)

TARGET_COMPANIES = (
    "Amazon",
    "Flipkart",
    "Google",
    "Microsoft",
    "Meta",
    "Apple",
    "Netflix",
    "Swiggy",
    "Zomato",
    "PhonePe",
    "Paytm",
    "Razorpay",
    "Infosys",
    "TCS",
    "Wipro",
    "Accenture",
    "IBM",
    "Oracle",
    "SAP",
    "Adobe",
    "Uber",
    "Ola",
    "Myntra",
    "Meesho",
    "Freshworks",
    "Zoho",
    "Thoughtworks",
    "Wissen Technology",
    "Motorola Solutions",
    "PwC India",
)


def _build_role_catalog() -> list[str]:
    catalog: list[str] = []
    seen: set[str] = set()
    for seed in ROLE_SEEDS:
        for suffix in ROLE_SUFFIXES:
            phrase = f"{seed} {suffix}".strip()
            key = phrase.lower()
            if key in seen:
                continue
            seen.add(key)
            catalog.append(phrase)
    return catalog


ROLE_CATALOG = _build_role_catalog()


def suggest_roles(query: str, *, limit: int = 12) -> list[str]:
    q = (query or "").strip().lower()
    if not q:
        return ROLE_CATALOG[:limit]
    return [r for r in ROLE_CATALOG if q in r.lower()][:limit]


def suggest_skills(query: str, *, limit: int = 12) -> list[str]:
    q = (query or "").strip().lower()
    if not q:
        return SKILLS_MASTER[:limit]
    return [s for s in SKILLS_MASTER if q in s.lower()][:limit]


def suggest_companies(query: str, *, limit: int = 12) -> list[str]:
    q = (query or "").strip().lower()
    pool = list(TARGET_COMPANIES)
    if not q:
        return pool[:limit]
    return [c for c in pool if q in c.lower()][:limit]


LOCATION_SUGGESTIONS = (
    "Remote",
    "Hybrid",
    "India",
    "Bangalore",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Mumbai",
    "Delhi NCR",
    "Gurgaon",
    "Noida",
    "Kolkata",
    "Ahmedabad",
    "Kochi",
    "Jaipur",
    "Indore",
    "Chandigarh",
)


def suggest_locations(query: str, *, limit: int = 12) -> list[str]:
    q = (query or "").strip().lower()
    pool = list(LOCATION_SUGGESTIONS)
    if not q:
        return pool[:limit]
    return [loc for loc in pool if q in loc.lower()][:limit]
