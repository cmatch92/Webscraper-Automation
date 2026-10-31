from typing import Optional

from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext

from .models import ScraperConfig

class BrowserManager:
    """
    Handles the lifecycle of the Playwright browser.
    Implemented as a singleton-style manager to avoid launching
    too many browser instances.
    """
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None

    async def start(self, headless: bool = True):
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if not self.browser:
            logger.info(f"Launching browser (headless={headless})...")
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
            )
        return self.browser

    async def get_context(self, config: ScraperConfig) -> BrowserContext:
        """Create a browser context with optional configured headers."""
        if not self.browser:
            await self.start()

        context = await self.browser.new_context(
            user_agent=config.headers.get("User-Agent"),
        )
        return context

    async def stop(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
