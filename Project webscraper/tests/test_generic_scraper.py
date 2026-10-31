import pytest
import asyncio
import json
from pathlib import Path
from src.core.models import ScraperConfig
from src.core.generic_scraper import GenericScraper

# Mock HTML for testing
MOCK_HTML = """
<html>
    <body>
        <div class="product-list">
            <div class="product-item">
                <span class="name">Product A</span>
                <span class="price">$10</span>
            </div>
            <div class="product-item">
                <span class="name">Product B</span>
                <span class="price">$20</span>
            </div>
            <div class="product-item">
                <span class="name">Product C</span>
                <span class="price">$30</span>
            </div>
        </div>
    </body>
</html>
"""

@pytest.mark.asyncio
async def test_generic_scraper_parsing():
    # Configure selectors
    selectors = {
        "container": ".product-item",
        "fields": {
            "name": ".name",
            "price": ".price"
        }
    }

    config = ScraperConfig(target_url="http://example.com")
    scraper = GenericScraper(config, selectors)

    results = await scraper.parse(MOCK_HTML)

    assert len(results) == 3
    assert results[0]["name"] == "Product A"
    assert results[0]["price"] == "$10"
    assert results[1]["name"] == "Product B"
    assert results[2]["price"] == "$30"

@pytest.mark.asyncio
async def test_generic_scraper_no_container():
    # Test case where no container is specified (single record)
    selectors = {
        "fields": {
            "title": "title"
        }
    }

    html = "<html><title>Hello World</title></html>"
    config = ScraperConfig(target_url="http://example.com")
    scraper = GenericScraper(config, selectors)

    results = await scraper.parse(html)

    assert len(results) == 1
    assert results[0]["title"] == "Hello World"

@pytest.mark.asyncio
async def test_generic_scraper_missing_fields():
    # Test case where some fields are missing in some records
    selectors = {
        "container": ".item",
        "fields": {
            "name": ".name",
            "desc": ".desc"
        }
    }

    html = """
    <div class="item"><span class="name">Item 1</span><span class="desc">Desc 1</span></div>
    <div class="item"><span class="name">Item 2</span></div>
    """
    config = ScraperConfig(target_url="http://example.com")
    scraper = GenericScraper(config, selectors)

    results = await scraper.parse(html)

    assert len(results) == 2
    assert results[0]["name"] == "Item 1"
    assert results[0]["desc"] == "Desc 1"
    assert results[1]["name"] == "Item 2"
    assert results[1]["desc"] is None


@pytest.mark.asyncio
async def test_generic_scraper_extracts_attributes():
    selectors = {
        "container": ".item",
        "fields": {
            "title": "h2",
            "url": {"selector": "a", "attribute": "href"},
            "description": {
                "selector": "meta[name='description']",
                "attribute": "content",
            },
        },
    }
    scraper = GenericScraper(ScraperConfig(target_url="https://example.com"), selectors)

    records = await scraper.parse(
        '<div class="item"><h2>Title</h2><a href="/detail">Details</a>'
        '<meta name="description" content="Description"></div>'
    )

    assert records == [{
        "title": "Title",
        "url": "/detail",
        "description": "Description",
    }]


def test_generic_scraper_rejects_empty_fields():
    with pytest.raises(ValueError, match="non-empty object"):
        GenericScraper(ScraperConfig(target_url="https://example.com"), {"fields": {}})


@pytest.mark.asyncio
async def test_generic_scraper_no_matching_container_is_an_error():
    scraper = GenericScraper(
        ScraperConfig(target_url="https://example.com"),
        {"container": ".missing", "fields": {"title": "h1"}},
    )

    with pytest.raises(ValueError, match="No records matched"):
        await scraper.parse("<html></html>")


@pytest.mark.asyncio
async def test_books_selectors_match_saved_demo_html():
    project_dir = Path(__file__).resolve().parents[1]
    selectors = json.loads(
        (project_dir / "config" / "books_toscrape.json").read_text(encoding="utf-8")
    )
    html = (project_dir / "tests" / "fixtures" / "books_demo.html").read_text(
        encoding="utf-8"
    )
    scraper = GenericScraper(
        ScraperConfig(target_url="https://books.toscrape.com/"), selectors
    )

    records = await scraper.parse(html, max_records=20)

    assert len(records) == 2
    assert records[0] == {
        "title": "Demo Book One",
        "price": "$12.34",
        "availability": "In stock",
        "product_url": "catalogue/demo-book-one_1/index.html",
        "rating": ["star-rating", "Three"],
    }
