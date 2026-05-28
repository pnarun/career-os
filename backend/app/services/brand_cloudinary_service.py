"""Upload Career OS brand PNGs to Cloudinary (optional; for email/CDN URLs)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinarySdkError

from app.core.brand_assets import LogoVariant, _FILENAMES, _STATIC_BRAND_DIR
from app.services.cloudinary_service import CloudinaryConfigError, configure_cloudinary

logger = logging.getLogger(__name__)

_FOLDER = "career_os/brand"


def upload_brand_logos_to_cloudinary() -> dict[LogoVariant, str]:
    """
    Upload full/black/symbol logos from app/static/brand.
    Returns secure_url per variant. Raises if Cloudinary is not configured.
    """
    configure_cloudinary()
    urls: dict[LogoVariant, str] = {}

    for variant, filename in _FILENAMES.items():
        path = _STATIC_BRAND_DIR / filename
        if not path.is_file():
            logger.warning("Brand file missing: %s", path)
            continue
        public_id = f"{_FOLDER}/{variant}"
        try:
            with path.open("rb") as handle:
                result: dict[str, Any] = cloudinary.uploader.upload(
                    handle,
                    resource_type="image",
                    public_id=public_id,
                    overwrite=True,
                    unique_filename=False,
                )
            secure = str(result.get("secure_url") or "").strip()
            if secure:
                urls[variant] = secure
                logger.info("Brand logo uploaded to Cloudinary: %s → %s", variant, secure)
        except CloudinarySdkError as exc:
            logger.error("Cloudinary brand upload failed for %s: %s", variant, exc)
            raise

    if not urls:
        raise CloudinaryConfigError("No brand logos were uploaded to Cloudinary")
    return urls
