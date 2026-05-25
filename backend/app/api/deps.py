"""Shared API dependencies."""

from fastapi import Depends

from app.auth.dependencies import CurrentUser, get_current_user

# Re-export for route modules
RequireUser = Depends(get_current_user)

__all__ = ["CurrentUser", "get_current_user", "RequireUser"]
