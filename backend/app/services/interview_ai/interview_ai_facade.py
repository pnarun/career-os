"""Interview AI orchestration — resolve resume, job, market context."""

from __future__ import annotations

from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import get_database
from app.models.application import ApplicationDocument
from app.models.job import JobDocument
from app.services.application_service import list_applications
from app.models.resume import ResumeDocument
from app.services.job_service import get_latest_scan_jobs
from app.services.resume_service import get_all_resumes, get_resume_by_id
from app.services.user_preferences_service import get_preferences


async def resolve_resume(resume_id: str = "") -> ResumeDocument | None:
    try:
        if resume_id.strip():
            return await get_resume_by_id(resume_id.strip())
        prefs = await get_preferences()
        if prefs and prefs.resume_id:
            return await get_resume_by_id(prefs.resume_id)
        resumes = await get_all_resumes()
        return resumes[0] if resumes else None
    except Exception:
        return None


async def get_job_by_id(job_id: str) -> JobDocument:
    try:
        object_id = ObjectId(job_id.strip())
    except InvalidId as exc:
        raise ValueError(f"Invalid job id: {job_id}") from exc
    document = await get_database()["jobs"].find_one({"_id": object_id})
    if not document:
        raise ValueError(f"Job not found: {job_id}")
    return JobDocument.from_mongo(document)


async def _find_application(job_id: str) -> ApplicationDocument | None:
    if not job_id.strip():
        return None
    for app in await list_applications():
        if app.job_id == job_id or app.application_id == job_id:
            return app
    return None


async def _description_from_application(app: ApplicationDocument) -> str:
    skills = ", ".join(app.matched_skills[:12]) if app.matched_skills else ""
    return (
        f"{app.title} at {app.company}. "
        f"Location: {app.location or 'unspecified'}. "
        f"{'Skills: ' + skills + '. ' if skills else ''}"
        f"Software engineering role requiring technical and behavioral interview preparation."
    )


async def resolve_job_context(
    *,
    job_id: str = "",
    job_description: str = "",
    job_title: str = "",
    company: str = "",
    job_location: str = "",
) -> tuple[str, str, str, str]:
    if job_id.strip():
        try:
            job = await get_job_by_id(job_id.strip())
            return (
                job.description or job_description,
                job.title or job_title,
                job.company or company,
                job.location or job_location,
            )
        except ValueError:
            app = await _find_application(job_id.strip())
            if app:
                description = job_description
                if len((description or "").strip()) < 20:
                    description = await _description_from_application(app)
                return (
                    description,
                    app.title or job_title,
                    app.company or company,
                    app.location or job_location,
                )
            raise ValueError(f"Job not found: {job_id}") from None
    if not job_description.strip():
        raise ValueError("job_id or job_description is required")
    return job_description, job_title, company, job_location


async def market_jobs_context() -> list[dict]:
    jobs = await get_latest_scan_jobs()
    return [
        {
            "title": j.title,
            "company": j.company,
            "description": j.description,
            "technologies": j.matched_skills,
            "missing_skills": j.missing_skills,
        }
        for j in jobs
    ]
