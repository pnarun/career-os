"""Resume AI orchestration — resolve resume + market context."""

from __future__ import annotations

from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import get_database
from app.models.job import JobDocument
from app.models.resume import ResumeDocument
from app.services.job_service import get_latest_scan_jobs
from app.services.resume_service import get_all_resumes, get_resume_by_id
from app.services.user_preferences_service import get_preferences


async def resolve_resume(resume_id: str = "") -> ResumeDocument:
    if resume_id.strip():
        return await get_resume_by_id(resume_id.strip())

    prefs = await get_preferences()
    if prefs and prefs.resume_id:
        return await get_resume_by_id(prefs.resume_id)

    resumes = await get_all_resumes()
    if not resumes:
        raise ValueError("No resumes found. Upload a resume first.")
    return resumes[0]


async def market_jobs_context() -> list[dict]:
    jobs = await get_latest_scan_jobs()
    return [
        {
            "title": j.title,
            "description": j.description,
            "missing_skills": j.missing_skills,
            "match_percentage": j.match_percentage,
            "source": j.source,
        }
        for j in jobs
    ]


async def get_job_by_id(job_id: str) -> JobDocument:
    try:
        object_id = ObjectId(job_id.strip())
    except InvalidId as exc:
        raise ValueError(f"Invalid job id: {job_id}") from exc

    document = await get_database()["jobs"].find_one({"_id": object_id})
    if not document:
        raise ValueError(f"Job not found: {job_id}")
    return JobDocument.from_mongo(document)


async def resolve_job_for_tailoring(
    *,
    job_id: str = "",
    job_description: str = "",
    job_title: str = "",
    job_location: str = "",
    job_remote: bool = False,
) -> tuple[str, str, str, str, bool]:
    if job_id.strip():
        job = await get_job_by_id(job_id.strip())
        return (
            job.description or job_description,
            job.title or job_title,
            job.location or job_location,
            job.remote_priority or job_remote,
        )
    if not job_description.strip():
        raise ValueError("job_id or job_description is required")
    return job_description, job_title, job_location, job_remote
