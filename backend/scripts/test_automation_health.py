import asyncio

from app.services.automation_service import check_browser_health


async def main() -> None:
    for i in range(2):
        result = await check_browser_health()
        print(i, result.status, result.chromium_version)


if __name__ == "__main__":
    asyncio.run(main())
