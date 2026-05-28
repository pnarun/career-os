import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_service import verify_access_token
from app.core.user_context import clear_request_user, set_request_user
from app.services.user_service import UserNotFoundError, get_user_by_id

_bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    workspace_id: str
    email: str
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = verify_access_token(credentials.credentials)
        user = await get_user_by_id(user_id)
    except (ValueError, UserNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Account is disabled"},
        )

    set_request_user(user.id, user.workspace_id, user.email)
    return CurrentUser(
        user_id=user.id,
        workspace_id=user.workspace_id,
        email=user.email,
        role=user.role,
    )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        clear_request_user()
        return None
