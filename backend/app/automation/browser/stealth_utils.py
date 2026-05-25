"""
Human-like interaction helpers for respectful automation pacing.

Not intended to bypass protections — reduces burst traffic and improves UX realism.
"""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page


async def human_delay(
    min_ms: float = 300,
    max_ms: float = 900,
) -> None:
    """Wait a randomized interval between actions."""
    delay = random.uniform(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)


async def type_like_human(
    locator: Locator,
    text: str,
    *,
    min_char_delay_ms: float = 40,
    max_char_delay_ms: float = 120,
) -> None:
    """Type text character-by-character with small random delays."""
    await locator.click()
    await human_delay(150, 350)

    for char in text:
        await locator.press(char, delay=0)
        delay = random.uniform(min_char_delay_ms, max_char_delay_ms) / 1000.0
        await asyncio.sleep(delay)


async def gradual_scroll(
    page: Page,
    *,
    steps: int = 5,
    step_px: int = 400,
    pause_min_ms: float = 200,
    pause_max_ms: float = 500,
) -> None:
    """Scroll down the page in small steps with pauses."""
    steps = max(1, steps)
    for _ in range(steps):
        await page.mouse.wheel(0, step_px)
        await human_delay(pause_min_ms, pause_max_ms)


async def move_mouse_naturally(
    page: Page,
    x: float,
    y: float,
    *,
    steps: int = 8,
) -> None:
    """Move mouse toward coordinates in small increments."""
    steps = max(1, steps)
    viewport = page.viewport_size or {"width": 1280, "height": 720}
    start_x = viewport["width"] / 2
    start_y = viewport["height"] / 2

    for i in range(1, steps + 1):
        t = i / steps
        ix = start_x + (x - start_x) * t
        iy = start_y + (y - start_y) * t
        await page.mouse.move(ix, iy)
        await human_delay(30, 80)
