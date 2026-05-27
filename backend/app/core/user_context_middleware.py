"""Attach authenticated user email to logs for every HTTP request."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.auth.jwt_service import verify_access_token
from app.core.user_context import clear_request_user, set_request_user
from app.services.user_service import UserNotFoundError, get_user_by_id


class UserContextMiddleware(BaseHTTPMiddleware):
    """Set request-scoped user (id, workspace, email) from Bearer JWT when present."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # BaseHTTPMiddleware breaks WebSocket upgrades (403). Auth is handled in realtime_router.
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
            if token:
                try:
                    user_id = verify_access_token(token)
                    user = await get_user_by_id(user_id)
                    if user.is_active:
                        set_request_user(user.id, user.workspace_id, user.email)
                except (ValueError, UserNotFoundError):
                    pass

        try:
            return await call_next(request)
        finally:
            clear_request_user()
