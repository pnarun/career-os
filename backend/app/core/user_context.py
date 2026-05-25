"""Request-scoped user identity for service-layer queries."""

from contextvars import ContextVar

current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)
current_workspace_id: ContextVar[str | None] = ContextVar("current_workspace_id", default=None)


def set_request_user(user_id: str, workspace_id: str = "") -> None:
    current_user_id.set(user_id)
    if workspace_id:
        current_workspace_id.set(workspace_id)


def clear_request_user() -> None:
    current_user_id.set(None)
    current_workspace_id.set(None)


def get_request_user_id() -> str | None:
    return current_user_id.get()


def get_request_workspace_id() -> str | None:
    return current_workspace_id.get()


def require_request_user_id() -> str:
    user_id = get_request_user_id()
    if not user_id:
        raise RuntimeError("Authenticated user context is required")
    return user_id
