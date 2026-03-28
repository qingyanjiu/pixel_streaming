import asyncio
import logging
from typing import Optional
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


@dataclass
class BrowserSession:
    id: str
    browser: Optional[Browser] = None
    page: Optional[Page] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def start(self):
        if self.browser:
            return
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({'width': 1920, 'height': 1080})
        logger.info(f'Session {self.id}: Browser started')

    async def navigate(self, url: str):
        if not self.page:
            raise RuntimeError('Browser not started')
        await self.page.goto(url, wait_until='networkidle')
        logger.info(f'Session {self.id}: Navigated to {url}')

    async def evaluate(self, script: str):
        if not self.page:
            raise RuntimeError('Browser not started')
        return await self.page.evaluate(script)

    async def capture_frame(self) -> Optional[bytes]:
        if not self.page:
            return None
        try:
            return await self.page.screenshot(type='jpeg', quality=80)
        except Exception as e:
            logger.error(f'Session {self.id}: Capture error: {e}')
            return None

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            logger.info(f'Session {self.id}: Browser closed')


class BrowserManager:
    def __init__(self):
        self.sessions: dict[str, BrowserSession] = {}
        self._playwright = None

    async def start(self):
        self._playwright = await async_playwright().start()
        logger.info('BrowserManager started')

    async def stop(self):
        for session in list(self.sessions.values()):
            await session.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info('BrowserManager stopped')

    def get_session(self, session_id: str) -> BrowserSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = BrowserSession(id=session_id)
        return self.sessions[session_id]

    async def close_session(self, session_id: str):
        if session_id in self.sessions:
            await self.sessions[session_id].close()
            del self.sessions[session_id]


browser_manager = BrowserManager()
