"""Extract interview-relevant topics from job descriptions."""

from __future__ import annotations

from typing import Any

from app.services.interview_ai._jd_utils import extract_jd_topics


def extract_topics(
    job_description: str,
    *,
    job_title: str = "",
    company: str = "",
) -> dict[str, Any]:
    topics = extract_jd_topics(job_description, job_title=job_title)
    return {
        **topics,
        "company": company,
        "job_title": job_title,
        "topic_count": len(topics.get("technologies", [])),
    }
