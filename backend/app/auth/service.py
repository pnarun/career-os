import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.auth.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.auth.schemas import AuthResponse, TokenResponse
from app.core.config import settings
from app.core.database import get_database
from app.models.user import UserPublic
from app.services.user_preferences_service import save_preferences
from app.services.user_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    authenticate_user,
    change_user_password,
    create_user,
    get_user_by_id,
    set_user_workspace,
    update_user_profile,
)
from app.services.workspace_service import create_workspace

logger = logging.getLogger(__name__)

REFRESH_TOKENS_COLLECTION = "auth_refresh_tokens"


class AuthServiceError(Exception):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_refresh_collection() -> AsyncIOMotorCollection:
    return get_database()[REFRESH_TOKENS_COLLECTION]


async def ensure_auth_indexes() -> None:
    collection = _get_refresh_collection()
    await collection.create_index("token_hash", unique=True)
    await collection.create_index("user_id")
    await collection.create_index("expires_at")


async def _store_refresh_token(user_id: str, refresh_token: str) -> None:
    expires_at = _utc_now() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    document = {
        "user_id": user_id,
        "token_hash": _hash_refresh_token(refresh_token),
        "expires_at": expires_at.isoformat(),
        "created_at": _utc_now().isoformat(),
        "revoked": False,
    }
    await _get_refresh_collection().insert_one(document)


async def _revoke_refresh_token(refresh_token: str) -> None:
    token_hash = _hash_refresh_token(refresh_token)
    await _get_refresh_collection().update_one(
        {"token_hash": token_hash},
        {"$set": {"revoked": True}},
    )


async def _is_refresh_token_valid(user_id: str, refresh_token: str) -> bool:
    token_hash = _hash_refresh_token(refresh_token)
    document = await _get_refresh_collection().find_one(
        {"token_hash": token_hash, "user_id": user_id, "revoked": False}
    )
    if not document:
        return False
    expires_raw = document.get("expires_at", "")
    try:
        expires_at = datetime.fromisoformat(expires_raw)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return expires_at > _utc_now()


def _build_tokens(user_id: str, workspace_id: str) -> TokenResponse:
    access = create_access_token(
        user_id,
        extra={"workspace_id": workspace_id},
    )
    refresh = create_refresh_token(user_id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def _link_existing_preferences(user_id: str, workspace_id: str, email: str) -> bool:
    """Attach orphan preferences/documents from pre-auth usage to the new account."""
    db = get_database()
    normalized = email.strip().lower()
    result = await db["user_preferences"].update_one(
        {
            "email": normalized,
            "$or": [{"user_id": {"$exists": False}}, {"user_id": ""}],
        },
        {"$set": {"user_id": user_id, "workspace_id": workspace_id}},
    )
    return result.modified_count > 0


async def register_user(
    email: str,
    password: str,
    *,
    full_name: str = "",
    timezone: str = "Asia/Kolkata",
) -> AuthResponse:
    try:
        user = await create_user(
            email,
            password,
            full_name=full_name,
            timezone=timezone,
        )
        workspace = await create_workspace(
            name=f"{full_name or email.split('@')[0]}'s Workspace",
            owner_id=user.id,
        )
        await set_user_workspace(user.id, workspace.id)
        user = await get_user_by_id(user.id)

        from app.models.user_preferences import UserPreferencesCreate

        linked = await _link_existing_preferences(user.id, workspace.id, user.email)
        if not linked:
            try:
                await save_preferences(
                    UserPreferencesCreate(
                        email=user.email,
                        resume_id="",
                        timezone=timezone,
                    ),
                    user_id=user.id,
                    workspace_id=workspace.id,
                )
            except Exception:
                logger.warning("Could not create default preferences for user=%s", user.id)

        tokens = _build_tokens(user.id, workspace.id)
        await _store_refresh_token(user.id, tokens.refresh_token)

        try:
            from app.services.admin_notify_service import notify_new_user_registration

            notify_new_user_registration(
                email=user.email,
                full_name=user.full_name or full_name,
                user_id=user.id,
                timezone=timezone,
            )
        except Exception:
            logger.exception("Admin new-user email failed for user=%s", user.id)

        return AuthResponse(
            **tokens.model_dump(),
            user=UserPublic.from_document(user),
        )
    except UserAlreadyExistsError:
        raise


async def login_user(email: str, password: str) -> AuthResponse:
    try:
        user = await authenticate_user(email, password)
    except InvalidCredentialsError:
        raise
    tokens = _build_tokens(user.id, user.workspace_id)
    await _store_refresh_token(user.id, tokens.refresh_token)
    return AuthResponse(
        **tokens.model_dump(),
        user=UserPublic.from_document(user),
    )


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    try:
        user_id = verify_refresh_token(refresh_token)
    except ValueError as exc:
        raise AuthServiceError(str(exc)) from exc

    token_hash = _hash_refresh_token(refresh_token)
    revoked = await _get_refresh_collection().find_one_and_update(
        {"token_hash": token_hash, "user_id": user_id, "revoked": False},
        {"$set": {"revoked": True}},
    )
    if not revoked:
        raise AuthServiceError("Refresh token revoked or expired")

    user = await get_user_by_id(user_id)
    if not user.is_active:
        raise AuthServiceError("Account is disabled")

    tokens = _build_tokens(user.id, user.workspace_id)
    try:
        await _store_refresh_token(user.id, tokens.refresh_token)
    except Exception as exc:
        from pymongo.errors import DuplicateKeyError

        if isinstance(exc, DuplicateKeyError):
            tokens = _build_tokens(user.id, user.workspace_id)
            await _store_refresh_token(user.id, tokens.refresh_token)
        else:
            raise
    return tokens


async def logout_user(refresh_token: str | None) -> None:
    if refresh_token:
        await _revoke_refresh_token(refresh_token)


async def get_me(user_id: str) -> UserPublic:
    user = await get_user_by_id(user_id)
    return UserPublic.from_document(user)


async def update_me(
    user_id: str,
    *,
    full_name: str,
    timezone: str,
) -> UserPublic:
    user = await update_user_profile(
        user_id,
        full_name=full_name,
        timezone=timezone,
    )
    return UserPublic.from_document(user)


async def update_password(
    user_id: str,
    *,
    current_password: str,
    new_password: str,
) -> None:
    await change_user_password(user_id, current_password, new_password)
