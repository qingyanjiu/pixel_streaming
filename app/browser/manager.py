import asyncio
import logging
from typing import Optional
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, Page
from app.config import Config

logger = logging.getLogger(__name__)


@dataclass
class BrowserSession:
    id: str
    browser: Optional[Browser] = None
    page: Optional[Page] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    viewport_width: int = 1920
    viewport_height: int = 1080

    async def start(self):
        if self.browser:
            return

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--enable-gpu",
                "--use-gl=angle",
                "--ignore-gpu-blocklist",
                "--enable-webgl",
                "--disable-frame-rate-limit",
                "--disable-gpu-sandbox",
            ],
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size(
            {"width": self.viewport_width, "height": self.viewport_height}
        )
        logger.info(
            f"Session {self.id}: Browser started with viewport {self.viewport_width}x{self.viewport_height}"
        )

    async def set_viewport_size(self, width: int, height: int):
        self.viewport_width = width
        self.viewport_height = height
        if self.page:
            await self.page.set_viewport_size({"width": width, "height": height})
        logger.info(f"Session {self.id}: Viewport set to {width}x{height}")

    async def navigate(self, url: str, timeout: float = 60.0):
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            await self.page.goto(
                url, wait_until="domcontentloaded", timeout=timeout * 1000
            )
            logger.info(f"Session {self.id}: Navigated to {url}")
        except Exception as e:
            logger.warning(
                f"Session {self.id}: Navigation timeout, continuing anyway: {e}"
            )

    async def evaluate(self, script: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        return await self.page.evaluate(script)

    async def capture_frame(self, quality: int = 80) -> Optional[bytes]:
        if not self.page:
            return None
        try:
            return await self.page.screenshot(type="jpeg", quality=quality)
        except Exception as e:
            logger.error(f"Session {self.id}: Capture error: {e}")
            return None

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            logger.info(f"Session {self.id}: Browser closed")

    async def mouse_move(self, x: float, y: float):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.mouse.move(x, y)

    async def mouse_click(
        self, x: float, y: float, button: str = "left", click_count: int = 1
    ):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.mouse.click(x, y, button=button, click_count=click_count)

    async def mouse_down(self, button: str = "left"):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.mouse.down(button=button)

    async def mouse_up(self, button: str = "left"):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.mouse.up(button=button)

    async def mouse_wheel(self, delta_x: int = 0, delta_y: int = 0):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.mouse.wheel(delta_x, delta_y)

    async def keyboard_down(self, key: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.keyboard.down(key)

    async def keyboard_up(self, key: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.keyboard.up(key)

    async def keyboard_press(self, key: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.keyboard.press(key)

    async def keyboard_type(self, text: str):
        if not self.page:
            raise RuntimeError("Browser not started")
        await self.page.keyboard.type(text)


class BrowserManager:
    def __init__(self):
        self.sessions: dict[str, BrowserSession] = {}
        self._playwright = None

    async def start(self):
        self._playwright = await async_playwright().start()
        logger.info("BrowserManager started")

    async def stop(self):
        for session in list(self.sessions.values()):
            await session.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("BrowserManager stopped")

    def get_session(self, session_id: str) -> BrowserSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = BrowserSession(id=session_id)
        return self.sessions[session_id]

    async def close_session(self, session_id: str):
        if session_id in self.sessions:
            await self.sessions[session_id].close()
            del self.sessions[session_id]


browser_manager = BrowserManager()
