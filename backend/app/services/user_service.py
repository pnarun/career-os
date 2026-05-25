import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.auth.password_service import hash_password, verify_password
from app.core.database import get_database
from app.models.user import UserDocument, UserRole

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users"


class UserServiceError(Exception):
    pass


class UserAlreadyExistsError(UserServiceError):
    pass


class UserNotFoundError(UserServiceError):
    pass


class InvalidCredentialsError(UserServiceError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[USERS_COLLECTION]


async def ensure_user_indexes() -> None:
    collection = _get_collection()
    await collection.create_index("email", unique=True)
    await collection.create_index("workspace_id")


async def create_user(
    email: str,
    password: str,
    *,
    full_name: str = "",
    timezone: str = "Asia/Kolkata",
    role: UserRole = "user",
    workspace_id: str = "",
) -> UserDocument:
    normalized = email.strip().lower()
    collection = _get_collection()
    existing = await collection.find_one({"email": normalized})
    if existing:
        raise UserAlreadyExistsError(f"Account already exists for {normalized}")

    now = _utc_now_iso()
    document: dict[str, Any] = {
        "email": normalized,
        "hashed_password": hash_password(password),
        "full_name": full_name.strip(),
        "timezone": timezone.strip() or "Asia/Kolkata",
        "created_at": now,
        "last_login": "",
        "is_active": True,
        "role": role,
        "workspace_id": workspace_id,
        "preferences": {},
    }
    result = await collection.insert_one(document)
    document["_id"] = result.inserted_id
    logger.info("User created email=%s id=%s", normalized, result.inserted_id)
    return UserDocument.from_mongo(document)


async def get_user_by_id(user_id: str) -> UserDocument:
    try:
        object_id = ObjectId(user_id)
    except InvalidId as exc:
        raise UserNotFoundError(f"Invalid user id: {user_id}") from exc

    document = await _get_collection().find_one({"_id": object_id})
    if not document:
        raise UserNotFoundError(f"User not found: {user_id}")
    return UserDocument.from_mongo(document)


async def get_user_by_email(email: str) -> UserDocument | None:
    normalized = email.strip().lower()
    document = await _get_collection().find_one({"email": normalized})
    if not document:
        return None
    return UserDocument.from_mongo(document)


async def get_user_with_password(email: str) -> tuple[UserDocument, str] | None:
    normalized = email.strip().lower()
    document = await _get_collection().find_one({"email": normalized})
    if not document:
        return None
    hashed = document.get("hashed_password", "")
    return UserDocument.from_mongo(document), hashed


async def authenticate_user(email: str, password: str) -> UserDocument:
    row = await get_user_with_password(email)
    if not row:
        raise InvalidCredentialsError("Invalid email or password")
    user, hashed = row
    if not user.is_active:
        raise InvalidCredentialsError("Account is disabled")
    if not verify_password(password, hashed):
        raise InvalidCredentialsError("Invalid email or password")
    await touch_last_login(user.id)
    return await get_user_by_id(user.id)


async def touch_last_login(user_id: str) -> None:
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        return
    await _get_collection().update_one(
        {"_id": object_id},
        {"$set": {"last_login": _utc_now_iso()}},
    )


async def set_user_workspace(user_id: str, workspace_id: str) -> None:
    try:
        object_id = ObjectId(user_id)
    except InvalidId as exc:
        raise UserNotFoundError(f"Invalid user id: {user_id}") from exc
    await _get_collection().update_one(
        {"_id": object_id},
        {"$set": {"workspace_id": workspace_id}},
    )


async def count_users() -> int:
    return await _get_collection().count_documents({})


async def update_user_profile(
    user_id: str,
    *,
    full_name: str,
    timezone: str,
) -> UserDocument:
    try:
        object_id = ObjectId(user_id)
    except InvalidId as exc:
        raise UserNotFoundError(f"Invalid user id: {user_id}") from exc

    update: dict[str, Any] = {
        "full_name": full_name.strip(),
        "timezone": timezone.strip() or "Asia/Kolkata",
    }
    result = await _get_collection().update_one({"_id": object_id}, {"$set": update})
    if result.matched_count == 0:
        raise UserNotFoundError(f"User not found: {user_id}")
    return await get_user_by_id(user_id)


async def change_user_password(
    user_id: str,
    current_password: str,
    new_password: str,
) -> None:
    row = await get_user_with_password_by_id(user_id)
    if not row:
        raise UserNotFoundError(f"User not found: {user_id}")
    user, hashed = row
    if not verify_password(current_password, hashed):
        raise InvalidCredentialsError("Current password is incorrect")

    try:
        object_id = ObjectId(user_id)
    except InvalidId as exc:
        raise UserNotFoundError(f"Invalid user id: {user_id}") from exc

    await _get_collection().update_one(
        {"_id": object_id},
        {"$set": {"hashed_password": hash_password(new_password)}},
    )
    logger.info("Password changed for user_id=%s", user_id)


async def get_user_with_password_by_id(user_id: str) -> tuple[UserDocument, str] | None:
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        return None
    document = await _get_collection().find_one({"_id": object_id})
    if not document:
        return None
    hashed = document.get("hashed_password", "")
    return UserDocument.from_mongo(document), hashed
