"""Master list of engineering skills and technologies for resume matching."""

from __future__ import annotations

import re

SKILLS_MASTER: list[str] = [
    "React",
    "Angular",
    "Vue.js",
    "Next.js",
    "TypeScript",
    "JavaScript",
    "HTML",
    "CSS",
    "Tailwind CSS",
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
    "MongoDB",
    "PostgreSQL",
    "MySQL",
    "Redis",
    "SQL",
    "NoSQL",
    "Elasticsearch",
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
    "Machine Learning",
    "TensorFlow",
    "PyTorch",
    "Pandas",
    "NumPy",
    "scikit-learn",
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

# Alternate spellings → canonical skill
SKILL_ALIASES: dict[str, str] = {
    "node": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "fast api": "FastAPI",
    "mongo": "MongoDB",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "k8s": "Kubernetes",
    "kube": "Kubernetes",
    "aws ec2": "AWS",
    "aws s3": "AWS",
    "aws lambda": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "ml": "Machine Learning",
    "ai": "Machine Learning",
    "rest": "REST API",
    "restful": "REST API",
    "graphql api": "GraphQL",
    "express": "Express.js",
    "expressjs": "Express.js",
    "springboot": "Spring Boot",
    "tailwind": "Tailwind CSS",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
}

TECH_STACK_GROUPS: dict[str, list[str]] = {
    "frontend": [
        "React",
        "Angular",
        "Vue.js",
        "Next.js",
        "TypeScript",
        "JavaScript",
        "HTML",
        "CSS",
        "Tailwind CSS",
    ],
    "backend": [
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
        "GraphQL",
        "REST API",
        "Microservices",
    ],
    "data": [
        "MongoDB",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "SQL",
        "NoSQL",
        "Elasticsearch",
        "Pandas",
        "NumPy",
    ],
    "cloud_devops": [
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
    ],
    "ml": [
        "Machine Learning",
        "TensorFlow",
        "PyTorch",
        "Pandas",
        "NumPy",
        "scikit-learn",
    ],
}

_SKILL_LOOKUP: dict[str, str] = {skill.lower(): skill for skill in SKILLS_MASTER}
for alias, canonical in SKILL_ALIASES.items():
    _SKILL_LOOKUP[alias.lower()] = canonical


def get_all_skills() -> list[str]:
    return list(SKILLS_MASTER)


def add_skills(skills: list[str]) -> None:
    for skill in skills:
        normalized = skill.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key not in _SKILL_LOOKUP:
            _SKILL_LOOKUP[key] = normalized
            SKILLS_MASTER.append(normalized)


def normalize_skill_term(term: str) -> str | None:
    cleaned = term.strip().lower()
    if not cleaned:
        return None
    return _SKILL_LOOKUP.get(cleaned)


def resolve_skill_match(term: str) -> str | None:
    return normalize_skill_term(term)


def _skill_pattern(skill: str) -> re.Pattern[str]:
    escaped = re.escape(skill)
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def _match_aliases(text: str, seen: set[str], matched: list[str]) -> None:
    text_lower = text.lower()
    for alias, canonical in SKILL_ALIASES.items():
        key = canonical.lower()
        if key in seen:
            continue
        if alias in text_lower or _skill_pattern(alias).search(text):
            seen.add(key)
            matched.append(canonical)


def extract_skills_from_text(text: str) -> list[str]:
    """Extract skills from free text using master list + aliases."""
    matched: list[str] = []
    seen: set[str] = set()

    for skill in SKILLS_MASTER:
        if _skill_pattern(skill).search(text):
            canonical = resolve_skill_match(skill) or skill
            key = canonical.lower()
            if key not in seen:
                seen.add(key)
                matched.append(canonical)

    _match_aliases(text, seen, matched)
    return sorted(matched, key=str.lower)


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    """Group skills into tech stack categories."""
    groups: dict[str, list[str]] = {name: [] for name in TECH_STACK_GROUPS}
    skill_set = {s.lower() for s in skills}
    for group_name, group_skills in TECH_STACK_GROUPS.items():
        for skill in group_skills:
            if skill.lower() in skill_set:
                groups[group_name].append(skill)
    return groups
