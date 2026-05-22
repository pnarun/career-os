import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.cloudinary_service import (
    CloudinaryConfigError,
    CloudinaryUploadError,
    upload_resume,
)
from app.services.resume_parser_service import ResumeParseError, parse_resume_from_url
from app.services.resume_service import (
    ResumeServiceError,
    build_resume_create,
    save_resume,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _validate_resume_file(file: UploadFile) -> str:
    """Validate resume file type and return a safe filename."""
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid file type. Only PDF and DOCX files are allowed.",
            },
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid content type. Only PDF and DOCX files are allowed.",
            },
        )

    return filename or f"resume{extension}"


@router.post("/upload-resume")
async def upload_resume_endpoint(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
) -> dict[str, Any]:
    """Upload, parse, persist, and return resume metadata."""
    original_filename = _validate_resume_file(file)

    try:
        file_data = await file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded resume")
        raise HTTPException(
            status_code=400,
            detail={"message": "Unable to read uploaded file"},
        ) from exc

    if len(file_data) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={"message": "File too large. Maximum size is 10 MB."},
        )

    try:
        upload_result = await upload_resume(file_data, original_filename)
    except CloudinaryConfigError as exc:
        logger.error("Cloudinary configuration error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "File upload service is not configured"},
        ) from exc
    except CloudinaryUploadError as exc:
        logger.error("Cloudinary upload error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"message": "Failed to upload resume. Please try again."},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during resume upload")
        raise HTTPException(
            status_code=500,
            detail={"message": "An unexpected error occurred during upload"},
        ) from exc

    try:
        parsed_profile = await parse_resume_from_url(
            upload_result["secure_url"],
            original_filename,
        )
    except ResumeParseError as exc:
        logger.error("Resume parsing failed after upload: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Resume uploaded but parsing failed. Please try again.",
                "resume_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during resume parsing")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Resume uploaded but an unexpected parsing error occurred.",
                "resume_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
            },
        ) from exc

    try:
        resume_payload = build_resume_create(upload_result, parsed_profile)
        saved_resume = await save_resume(resume_payload)
    except ResumeServiceError as exc:
        logger.error("Resume persistence failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Resume uploaded and parsed but failed to save to database.",
                "resume_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
                "parsed_profile": parsed_profile,
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during resume persistence")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Resume uploaded and parsed but an unexpected save error occurred.",
                "resume_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
                "parsed_profile": parsed_profile,
            },
        ) from exc

    return {
        "message": "Resume uploaded successfully",
        "resume_id": saved_resume.id,
        "upload": {
            "resume_url": upload_result["secure_url"],
            "public_id": upload_result["public_id"],
            "filename": upload_result["original_filename"],
        },
        "parsed_profile": parsed_profile,
        "resume": saved_resume.model_dump(),
    }
