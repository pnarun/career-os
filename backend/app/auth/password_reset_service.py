import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorCollection

from app.auth.password_service import hash_password
from app.core.config import settings
from app.core.database import get_database
from app.services.email_service import EmailNotConfiguredError, send_password_reset_otp
from app.services.user_service import get_user_by_email

logger = logging.getLogger(__name__)

OTP_COLLECTION = "password_reset_otps"
OTP_LENGTH = 6
OTP_TTL_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
MAX_VERIFY_ATTEMPTS = 5


class PasswordResetError(Exception):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[OTP_COLLECTION]


def _hash_otp(email: str, otp: str) -> str:
    payload = f"{email.strip().lower()}:{otp}:{settings.JWT_SECRET_KEY}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _generate_otp() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))


async def ensure_password_reset_indexes() -> None:
    collection = _get_collection()
    await collection.create_index("email")
    await collection.create_index("expires_at", expireAfterSeconds=0)


async def check_email_registered(email: str) -> bool:
    user = await get_user_by_email(email)
    return user is not None


async def request_password_reset_otp(email: str) -> dict[str, str | bool]:
    normalized = email.strip().lower()
    user = await get_user_by_email(normalized)
    if not user:
        raise PasswordResetError("No account found for this email.")

    collection = _get_collection()
    existing = await collection.find_one({"email": normalized}, sort=[("created_at", -1)])
    if existing:
        try:
            created = datetime.fromisoformat(existing.get("created_at", ""))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if (_utc_now() - created).total_seconds() < OTP_RESEND_COOLDOWN_SECONDS:
                raise PasswordResetError("Please wait a minute before requesting another code.")
        except ValueError:
            pass

    otp = _generate_otp()
    expires_at = _utc_now() + timedelta(minutes=OTP_TTL_MINUTES)
    document = {
        "email": normalized,
        "otp_hash": _hash_otp(normalized, otp),
        "expires_at": expires_at,
        "created_at": _utc_now_iso(),
        "attempts": 0,
        "verified": False,
    }
    await collection.insert_one(document)

    dev_expose = settings.AUTH_DEV_EXPOSE_OTP
    try:
        send_password_reset_otp(normalized, otp)
    except EmailNotConfiguredError:
        if dev_expose:
            logger.warning("Resend not configured — OTP for %s: %s", normalized, otp)
        else:
            raise PasswordResetError(
                "Email delivery is not configured. Contact support or try again later."
            ) from None

    result: dict[str, str | bool] = {
        "status": "ok",
        "message": "Verification code sent to your email.",
        "expires_in_minutes": OTP_TTL_MINUTES,
    }
    if dev_expose:
        result["dev_otp"] = otp
    return result


async def reset_password_with_otp(email: str, otp: str, new_password: str) -> None:
    normalized = email.strip().lower()
    if len(new_password) < 8:
        raise PasswordResetError("Password must be at least 8 characters.")

    user = await get_user_by_email(normalized)
    if not user:
        raise PasswordResetError("Invalid verification code.")

    collection = _get_collection()
    record = await collection.find_one({"email": normalized}, sort=[("created_at", -1)])
    if not record:
        raise PasswordResetError("Invalid or expired verification code.")

    expires_at = record.get("expires_at")
    if isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < _utc_now():
            raise PasswordResetError("Verification code expired. Request a new one.")

    attempts = int(record.get("attempts", 0))
    if attempts >= MAX_VERIFY_ATTEMPTS:
        raise PasswordResetError("Too many attempts. Request a new code.")

    if _hash_otp(normalized, otp.strip()) != record.get("otp_hash"):
        await collection.update_one(
            {"_id": record["_id"]},
            {"$inc": {"attempts": 1}},
        )
        raise PasswordResetError("Invalid verification code.")

    from bson import ObjectId

    await get_database()["users"].update_one(
        {"_id": ObjectId(user.id)},
        {"$set": {"hashed_password": hash_password(new_password)}},
    )
    await collection.delete_many({"email": normalized})
    logger.info("Password reset completed for email=%s", normalized)
