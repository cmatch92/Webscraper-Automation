import httpx
import pytest

from src.core.generic_scraper import GenericScraper
from src.core.models import ScraperConfig
from src.core import engine


REAL_ASYNC_CLIENT = httpx.AsyncClient


@pytest.mark.asyncio
async def test_http_fetch_disables_redirects_and_environment_proxies(monkeypatch):
    observed = {}

    def client_factory(**kwargs):
        observed.update(kwargs)
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, text="<h1>Ready</h1>")
        )
        return REAL_ASYNC_CLIENT(transport=transport, **kwargs)

    monkeypatch.setattr(engine.httpx, "AsyncClient", client_factory)
    scraper = GenericScraper(
        ScraperConfig(target_url="https://public.example"),
        {"fields": {"title": "h1"}},
    )

    content = await scraper.fetch()

    assert "<h1>Ready</h1>" in content
    assert observed["follow_redirects"] is False
    assert observed["trust_env"] is False


@pytest.mark.asyncio
async def test_http_fetch_rejects_redirects(monkeypatch):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"Location": "http://127.0.0.1"})
    )
    monkeypatch.setattr(
        engine.httpx,
        "AsyncClient",
        lambda **kwargs: REAL_ASYNC_CLIENT(transport=transport, **kwargs),
    )
    scraper = GenericScraper(
        ScraperConfig(target_url="https://public.example"),
        {"fields": {"title": "h1"}},
    )

    with pytest.raises(httpx.HTTPStatusError):
        await scraper.fetch()


@pytest.mark.asyncio
async def test_http_fetch_rejects_large_responses(monkeypatch):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"Content-Length": str(5 * 1024 * 1024 + 1)},
            content=b"",
        )
    )
    monkeypatch.setattr(
        engine.httpx,
        "AsyncClient",
        lambda **kwargs: REAL_ASYNC_CLIENT(transport=transport, **kwargs),
    )
    scraper = GenericScraper(
        ScraperConfig(target_url="https://public.example"),
        {"fields": {"title": "h1"}},
    )

    with pytest.raises(ValueError, match="5 MiB"):
        await scraper.fetch()
