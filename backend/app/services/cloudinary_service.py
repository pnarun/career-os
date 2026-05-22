import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, BinaryIO, TypedDict

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinarySdkError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RESUME_FOLDER = "career_os/resumes"
RESOURCE_TYPE = "raw"
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

_PLACEHOLDER_MARKERS = ("your_", "<", ">")


class CloudinaryConfigError(Exception):
    """Raised when Cloudinary environment configuration is missing or invalid."""


class CloudinaryUploadError(Exception):
    """Raised when a resume upload to Cloudinary fails."""


class CloudinaryDeleteError(Exception):
    """Raised when deleting a resume from Cloudinary fails."""


class ResumeUploadResult(TypedDict):
    secure_url: str
    public_id: str
    original_filename: str


def sanitize_filename(filename: str) -> str:
    """Normalize resume filenames for safe Cloudinary storage."""
    path = Path(filename or "resume.pdf")
    extension = path.suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        extension = ".pdf"

    stem = path.stem.lower().replace(" ", "_")
    stem = re.sub(r"[^a-z0-9._-]", "", stem)
    stem = stem.strip("._-") or "resume"

    return f"{stem}{extension}"


def _build_public_id(sanitized_filename: str) -> tuple[str, str | None]:
    """Return Cloudinary public_id and optional raw format."""
    stem = Path(sanitized_filename).stem
    extension = Path(sanitized_filename).suffix.lower().lstrip(".")
    public_id = f"{RESUME_FOLDER}/{stem}"
    return public_id, extension or None


def _get_cloudinary_credentials() -> tuple[str, str, str]:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()

    if not cloud_name or not api_key or not api_secret:
        raise CloudinaryConfigError(
            "Cloudinary credentials are not set. "
            "Configure CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and "
            "CLOUDINARY_API_SECRET in backend/.env"
        )

    for value, name in (
        (cloud_name, "CLOUDINARY_CLOUD_NAME"),
        (api_key, "CLOUDINARY_API_KEY"),
        (api_secret, "CLOUDINARY_API_SECRET"),
    ):
        if any(marker in value for marker in _PLACEHOLDER_MARKERS):
            raise CloudinaryConfigError(
                f"{name} contains placeholder values. Set real Cloudinary credentials in .env"
            )

    return cloud_name, api_key, api_secret


def configure_cloudinary() -> None:
    """Apply Cloudinary SDK configuration from environment variables."""
    cloud_name, api_key, api_secret = _get_cloudinary_credentials()
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    logger.debug("Cloudinary SDK configured for cloud: %s", cloud_name)


def _upload_resume_sync(
    file_data: bytes | BinaryIO,
    original_filename: str,
) -> ResumeUploadResult:
    configure_cloudinary()

    sanitized_filename = sanitize_filename(original_filename)
    public_id, file_format = _build_public_id(sanitized_filename)

    upload_options: dict[str, Any] = {
        "resource_type": RESOURCE_TYPE,
        "public_id": public_id,
        "use_filename": True,
        "unique_filename": False,
        "overwrite": True,
    }
    if file_format:
        upload_options["format"] = file_format

    try:
        result: dict[str, Any] = cloudinary.uploader.upload(
            file_data,
            **upload_options,
        )
    except CloudinarySdkError as exc:
        logger.exception(
            "Cloudinary upload failed for %s (sanitized: %s)",
            original_filename,
            sanitized_filename,
        )
        raise CloudinaryUploadError("Failed to upload resume to Cloudinary") from exc

    secure_url = result.get("secure_url")
    result_public_id = result.get("public_id")

    if not secure_url or not result_public_id:
        logger.error("Unexpected Cloudinary response: %s", result)
        raise CloudinaryUploadError("Cloudinary returned an incomplete upload response")

    logger.info(
        "Resume uploaded to Cloudinary: public_id=%s filename=%s",
        result_public_id,
        sanitized_filename,
    )
    return ResumeUploadResult(
        secure_url=secure_url,
        public_id=result_public_id,
        original_filename=sanitized_filename,
    )


def _delete_resume_sync(public_id: str) -> None:
    configure_cloudinary()

    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=RESOURCE_TYPE)
    except CloudinarySdkError as exc:
        logger.exception("Cloudinary delete failed for public_id=%s", public_id)
        raise CloudinaryDeleteError("Failed to delete resume from Cloudinary") from exc

    if result.get("result") != "ok":
        logger.warning(
            "Cloudinary delete returned non-ok result for %s: %s", public_id, result
        )
        raise CloudinaryDeleteError(f"Cloudinary could not delete asset: {public_id}")

    logger.info("Resume deleted from Cloudinary: public_id=%s", public_id)


async def upload_resume(
    file_data: bytes,
    original_filename: str,
) -> ResumeUploadResult:
    """Upload a resume file to Cloudinary (async wrapper)."""
    if not file_data:
        raise CloudinaryUploadError("Resume file is empty")

    return await asyncio.to_thread(
        _upload_resume_sync,
        file_data,
        original_filename,
    )


async def delete_resume(public_id: str) -> None:
    """Delete a resume from Cloudinary by public_id (async wrapper)."""
    if not public_id.strip():
        raise CloudinaryDeleteError("public_id is required")

    await asyncio.to_thread(_delete_resume_sync, public_id)
