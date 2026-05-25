from typing import Any

from app.realtime.websocket_manager import publish_user_event


async def emit_provider_started(user_id: str, *, provider: str, scan_id: str = "") -> None:
    await publish_user_event(
        user_id,
        "provider_started",
        provider=provider,
        scan_id=scan_id,
        status="running",
        message=f"{provider.title()} scan started",
    )


async def emit_provider_status(
    user_id: str,
    *,
    provider: str,
    status: str,
    count: int = 0,
    error: str = "",
    scan_id: str = "",
    **extra: Any,
) -> None:
    await publish_user_event(
        user_id,
        "provider_status",
        provider=provider,
        status=status,
        count=count,
        error=error,
        scan_id=scan_id,
        message=error or f"{provider.title()} {status}" + (f" ({count} jobs)" if count else ""),
        **extra,
    )


async def emit_provider_batch(
    user_id: str,
    *,
    providers: list[dict[str, Any]],
    scan_id: str = "",
) -> None:
    await publish_user_event(
        user_id,
        "provider_batch",
        providers=providers,
        scan_id=scan_id,
    )
