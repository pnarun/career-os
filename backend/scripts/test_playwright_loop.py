import asyncio

from playwright.async_api import async_playwright


async def main() -> None:
    loop = asyncio.get_running_loop()
    print("loop:", type(loop).__name__)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        print("version:", browser.version)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
