import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import CurrentUser, get_current_user
from app.auth.password_reset_service import (
    PasswordResetError,
    check_email_registered,
    ensure_password_reset_indexes,
    request_password_reset_otp,
    reset_password_with_otp,
)
from app.auth.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    CheckEmailRequest,
    CheckEmailResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
)
from app.auth.service import (
    AuthServiceError,
    get_me,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    update_me,
    update_password,
)
from app.models.user import UserPublic
from app.services.user_service import UserAlreadyExistsError, UserServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/check-email", response_model=CheckEmailResponse)
async def check_email(payload: CheckEmailRequest) -> CheckEmailResponse:
    email = str(payload.email).strip().lower()
    exists = await check_email_registered(email)
    return CheckEmailResponse(exists=exists, email=email)


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
async def password_reset_request(payload: PasswordResetRequest) -> PasswordResetRequestResponse:
    try:
        result = await request_password_reset_otp(str(payload.email))
        return PasswordResetRequestResponse(
            status=str(result["status"]),
            message=str(result["message"]),
            expires_in_minutes=int(result.get("expires_in_minutes", 10)),
            dev_otp=str(result["dev_otp"]) if result.get("dev_otp") else None,
        )
    except PasswordResetError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.post("/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirmRequest) -> dict[str, str]:
    try:
        await reset_password_with_otp(
            str(payload.email),
            payload.otp,
            payload.new_password,
        )
        return {"status": "ok", "message": "Password updated. You can sign in now."}
    except PasswordResetError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest) -> AuthResponse:
    try:
        return await register_user(
            str(payload.email),
            payload.password,
            full_name=payload.full_name,
            timezone=payload.timezone,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail={"message": str(exc)}) from exc
    except UserServiceError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Register failed")
        raise HTTPException(status_code=500, detail={"message": "Registration failed"}) from exc


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    from app.services.user_service import InvalidCredentialsError

    try:
        return await login_user(str(payload.email), payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail={"message": str(exc)}) from exc
    except Exception as exc:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail={"message": "Login failed"}) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest) -> TokenResponse:
    try:
        return await refresh_tokens(payload.refresh_token)
    except AuthServiceError as exc:
        raise HTTPException(status_code=401, detail={"message": str(exc)}) from exc


@router.post("/logout")
async def logout(payload: LogoutRequest) -> dict[str, str]:
    await logout_user(payload.refresh_token)
    return {"status": "ok"}


@router.get("/workspaces")
async def list_workspaces(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    from app.services.workspace_service import list_workspaces_for_user

    workspaces = await list_workspaces_for_user(current_user.user_id)
    return {
        "workspaces": [
            {"id": w.id, "name": w.name, "owner_id": w.owner_id}
            for w in workspaces
        ],
        "active_workspace_id": current_user.workspace_id,
    }


@router.get("/me", response_model=UserPublic)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> UserPublic:
    return await get_me(current_user.user_id)


@router.patch("/me", response_model=UserPublic)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> UserPublic:
    from app.services.user_service import UserNotFoundError

    try:
        return await update_me(
            current_user.user_id,
            full_name=payload.full_name,
            timezone=payload.timezone,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc


@router.patch("/password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    from app.services.user_service import InvalidCredentialsError, UserNotFoundError

    try:
        await update_password(
            current_user.user_id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        return {"status": "ok", "message": "Password updated successfully."}
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

