"""Master list of engineering skills and technologies for resume matching.

Extend SKILLS_MASTER or register additional skills via add_skills() at runtime.
"""

from __future__ import annotations

import re

SKILLS_MASTER: list[str] = [
    # Frontend
    "React",
    "Angular",
    "Vue.js",
    "Next.js",
    "TypeScript",
    "JavaScript",
    "HTML",
    "CSS",
    "Tailwind CSS",
    # Backend
    "Node.js",
    "Python",
    "FastAPI",
    "Django",
    "Flask",
    "Express.js",
    "Java",
    "Spring Boot",
    "Go",
    "Ruby",
    "Ruby on Rails",
    # Databases
    "MongoDB",
    "PostgreSQL",
    "MySQL",
    "Redis",
    "SQL",
    "NoSQL",
    "Elasticsearch",
    # Cloud & DevOps
    "AWS",
    "Azure",
    "Google Cloud",
    "GCP",
    "Docker",
    "Kubernetes",
    "Linux",
    "CI/CD",
    "Terraform",
    "Ansible",
    "Jenkins",
    "GitHub Actions",
    # Data & ML
    "Machine Learning",
    "TensorFlow",
    "PyTorch",
    "Pandas",
    "NumPy",
    "scikit-learn",
    # Tools & practices
    "Git",
    "REST API",
    "GraphQL",
    "Microservices",
    "Agile",
    "Scrum",
    "Jira",
    "Postman",
    "Kafka",
    "RabbitMQ",
    "Celery",
    "Playwright",
    "Selenium",
    "Unit Testing",
    "TDD",
]

# Normalized lookup: lowercase -> canonical display name
_SKILL_LOOKUP: dict[str, str] = {skill.lower(): skill for skill in SKILLS_MASTER}


def get_all_skills() -> list[str]:
    """Return a copy of the current skills master list."""
    return list(SKILLS_MASTER)


def add_skills(skills: list[str]) -> None:
    """Register additional skills without duplicates (case-insensitive)."""
    for skill in skills:
        normalized = skill.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key not in _SKILL_LOOKUP:
            _SKILL_LOOKUP[key] = normalized
            SKILLS_MASTER.append(normalized)


def resolve_skill_match(term: str) -> str | None:
    """Return canonical skill name if term matches the master list."""
    return _SKILL_LOOKUP.get(term.strip().lower())


def _skill_pattern(skill: str) -> re.Pattern[str]:
    escaped = re.escape(skill)
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def extract_skills_from_text(text: str) -> list[str]:
    """Extract skills from free text using the master skills list."""
    matched: list[str] = []
    seen: set[str] = set()

    for skill in SKILLS_MASTER:
        if _skill_pattern(skill).search(text):
            canonical = resolve_skill_match(skill) or skill
            key = canonical.lower()
            if key not in seen:
                seen.add(key)
                matched.append(canonical)

    return sorted(matched, key=str.lower)
