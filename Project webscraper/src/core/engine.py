from abc import ABC, abstractmethod
from typing import Any

import httpx
from loguru import logger

from .models import ScraperConfig, ScrapedData

class BaseScraper(ABC):
    """
    Abstract Base Class for all scrapers.
    Defines the standard workflow: Fetch -> Parse -> Validate.
    """
    def __init__(self, config: ScraperConfig):
        self.config = config

    async def fetch(self) -> str:
        if self.config.use_browser:
            raise ValueError("Browser-based fetching is disabled.")
        return await self._fetch_with_http()

    async def _fetch_with_http(self) -> str:
        """Fetch a bounded HTML response without following redirects or using proxies."""
        logger.info(f"Fetching {self.config.target_url} via HTTP...")
        async with httpx.AsyncClient(
            timeout=self.config.timeout / 1000,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            async with client.stream(
                "GET",
                self.config.target_url,
                headers=self.config.headers,
            ) as response:
                response.raise_for_status()
                max_response_bytes = 5 * 1024 * 1024
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > max_response_bytes:
                    raise ValueError("Response exceeds the 5 MiB size limit.")

                chunks = []
                total_bytes = 0
                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > max_response_bytes:
                        raise ValueError("Response exceeds the 5 MiB size limit.")
                    chunks.append(chunk)

                return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")

    @abstractmethod
    async def parse(self, html: str) -> Any:
        pass

    async def run(self) -> ScrapedData:
        """
        The main entry point for the scraper.
        """
        try:
            html = await self.fetch()
            data = await self.parse(html)

            return ScrapedData(
                source_url=self.config.target_url,
                data=data
            )
        except Exception:
            logger.exception(f"Scraper failed for {self.config.target_url}")
            raise
