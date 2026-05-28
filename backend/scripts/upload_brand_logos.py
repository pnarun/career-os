#!/usr/bin/env python3
"""Upload brand PNGs to Cloudinary and print env vars for Render/.env."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as: python scripts/upload_brand_logos.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.brand_cloudinary_service import upload_brand_logos_to_cloudinary


def main() -> None:
    urls = upload_brand_logos_to_cloudinary()
    print("\nAdd these to backend/.env or Render:\n")
    mapping = {
        "full": "BRAND_LOGO_FULL_URL",
        "black": "BRAND_LOGO_BLACK_URL",
        "symbol": "BRAND_LOGO_SYMBOL_URL",
    }
    for variant, env_key in mapping.items():
        url = urls.get(variant, "")
        if url:
            print(f"{env_key}={url}")
    print("\nAPI dev pages still use /brand/* locally; emails use the URLs above.\n")


if __name__ == "__main__":
    main()
