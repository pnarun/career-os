"""
Backfill legacy single-user data into the default migrated user/workspace.

Runs once on startup when users collection is empty or legacy data lacks user_id.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from app.auth.password_service import hash_password
from app.automation.browser.session_manager import PROFILES_DIR, SUPPORTED_PLATFORMS
from app.core.config import settings
from app.core.database import get_database
from app.services.user_service import USERS_COLLECTION, create_user, count_users
from app.services.workspace_service import create_workspace
from app.services.user_service import set_user_workspace

logger = logging.getLogger(__name__)

USER_SCOPED_COLLECTIONS = (
    "user_preferences",
    "resumes",
    "jobs",
    "scan_sessions",
    "applications",
    "notifications",
    "automation_runs",
    "career_insights",
    "apply_sessions",
    "apply_history",
    "apply_errors",
    "interview_prep_progress",
    "copilot_insights",
    "copilot_sessions",
)

MIGRATION_MARKER_COLLECTION = "platform_migrations"
MIGRATION_KEY = "legacy_user_v1"


async def _migration_done() -> bool:
    doc = await get_database()[MIGRATION_MARKER_COLLECTION].find_one({"key": MIGRATION_KEY})
    return bool(doc and doc.get("completed"))


async def _mark_migration_done(user_id: str, workspace_id: str) -> None:
    await get_database()[MIGRATION_MARKER_COLLECTION].update_one(
        {"key": MIGRATION_KEY},
        {
            "$set": {
                "key": MIGRATION_KEY,
                "completed": True,
                "user_id": user_id,
                "workspace_id": workspace_id,
            }
        },
        upsert=True,
    )


def _migrate_automation_profiles(user_id: str) -> None:
    """Move global platform session files into per-user directory."""
    sessions_root = PROFILES_DIR / "sessions" / user_id
    sessions_root.mkdir(parents=True, exist_ok=True)
    for platform in SUPPORTED_PLATFORMS:
        legacy = PROFILES_DIR / f"{platform}_session.json"
        target = sessions_root / f"{platform}_session.json"
        if legacy.is_file() and not target.exists():
            try:
                shutil.copy2(legacy, target)
                logger.info("Migrated automation session %s -> %s", legacy, target)
            except OSError as exc:
                logger.warning("Could not migrate session %s: %s", legacy, exc)


async def _backfill_collection(
    collection_name: str,
    user_id: str,
    workspace_id: str,
) -> int:
    collection = get_database()[collection_name]
    result = await collection.update_many(
        {"$or": [{"user_id": {"$exists": False}}, {"user_id": ""}]},
        {"$set": {"user_id": user_id, "workspace_id": workspace_id}},
    )
    return result.modified_count


async def _resolve_migration_email(db) -> str:
    """Prefer email from existing preferences (real prior usage)."""
    prefs = await db["user_preferences"].find_one(sort=[("updated_at", -1)])
    if prefs and prefs.get("email"):
        return str(prefs["email"]).strip().lower()
    return settings.LEGACY_MIGRATION_EMAIL.strip().lower()


async def run_legacy_data_migration() -> None:
    db = get_database()

    user_count = await count_users()
    needs_backfill = False
    for name in USER_SCOPED_COLLECTIONS:
        doc = await db[name].find_one(
            {"$or": [{"user_id": {"$exists": False}}, {"user_id": ""}]},
            projection={"_id": 1},
        )
        if doc:
            needs_backfill = True
            break

    if await _migration_done() and user_count > 0 and not needs_backfill:
        return

    if user_count == 0:
        email = await _resolve_migration_email(db)
        password = settings.LEGACY_MIGRATION_PASSWORD or "ChangeMe123!"
        try:
            user = await create_user(
                email,
                password,
                full_name="Career OS User",
                timezone="Asia/Kolkata",
                role="admin",
            )
        except Exception:
            logger.exception("Failed to create migration user for email=%s", email)
            raise
        workspace = await create_workspace("My Workspace", user.id)
        await set_user_workspace(user.id, workspace.id)
        user_id = user.id
        workspace_id = workspace.id
        logger.info(
            "Created account for existing data: email=%s id=%s — sign in and change password",
            email,
            user_id,
        )
    else:
        # Use first admin or any user as owner for orphan data
        doc = await db[USERS_COLLECTION].find_one(sort=[("created_at", 1)])
        user_id = str(doc["_id"])
        workspace_id = doc.get("workspace_id", "")
        if not workspace_id:
            workspace = await create_workspace("Default Workspace", user_id)
            workspace_id = workspace.id
            await set_user_workspace(user_id, workspace_id)

    total = 0
    for name in USER_SCOPED_COLLECTIONS:
        try:
            modified = await _backfill_collection(name, user_id, workspace_id)
            if modified:
                logger.info("Backfilled %s documents in %s", modified, name)
            total += modified
        except Exception:
            logger.exception("Backfill failed for collection %s", name)

    _migrate_automation_profiles(user_id)

    await _mark_migration_done(user_id, workspace_id)
    logger.info("Legacy data migration complete (%s documents updated)", total)


async def seed_demo_users() -> None:
    if not settings.AUTH_SEED_DEMO_USERS:
        return

    demos = (
        ("admin@career-os.demo", "Admin Demo", "admin", "Admin123!"),
        ("user@career-os.demo", "Demo User", "user", "User123!"),
    )
    for email, full_name, role, password in demos:
        from app.services.user_service import get_user_by_email

        if await get_user_by_email(email):
            continue
        try:
            from app.auth.service import register_user

            await register_user(email, password, full_name=full_name, timezone="Asia/Kolkata")
            # Promote admin role
            if role == "admin":
                await get_database()[USERS_COLLECTION].update_one(
                    {"email": email},
                    {"$set": {"role": "admin"}},
                )
            logger.info("Seeded demo user %s", email)
        except Exception:
            logger.exception("Failed to seed demo user %s", email)
