from typing import Any

from bs4 import BeautifulSoup
from loguru import logger
from soupsieve import SelectorSyntaxError

from .engine import BaseScraper
from .models import ScrapedData, ScraperConfig


class GenericScraper(BaseScraper):
    """Extract records from HTML using a container and field CSS selectors."""

    def __init__(self, config: ScraperConfig, selectors: dict[str, Any]):
        super().__init__(config)
        if not isinstance(selectors, dict):
            raise ValueError("Config must be a JSON object.")
        if set(selectors) - {"container", "fields"}:
            raise ValueError("Config supports only 'container' and 'fields' keys.")

        container = selectors.get("container")
        if container is not None and (not isinstance(container, str) or not container.strip()):
            raise ValueError("'container' must be a non-empty CSS selector string.")

        fields = selectors.get("fields")
        if not isinstance(fields, dict) or not fields:
            raise ValueError("'fields' must be a non-empty object of field selectors.")

        for field_name, definition in fields.items():
            if not isinstance(field_name, str) or not field_name.strip():
                raise ValueError("Field names must be non-empty strings.")
            if isinstance(definition, str):
                selector = definition
            elif isinstance(definition, dict):
                if set(definition) - {"selector", "attribute"}:
                    raise ValueError(f"Unsupported selector options for field '{field_name}'.")
                selector = definition.get("selector")
                attribute = definition.get("attribute", "text")
                if not isinstance(attribute, str) or not attribute.strip():
                    raise ValueError(f"Attribute for field '{field_name}' must be a string.")
            else:
                raise ValueError(
                    f"Selector for field '{field_name}' must be a string or selector object."
                )
            if not isinstance(selector, str) or not selector.strip():
                raise ValueError(f"Selector for field '{field_name}' must be non-empty.")

        self.selectors = selectors

    async def parse(
        self, html: str, max_records: int | None = None
    ) -> list[dict[str, Any]]:
        if max_records is not None and (
            isinstance(max_records, bool) or not isinstance(max_records, int) or max_records < 1
        ):
            raise ValueError("max_records must be a positive integer.")

        soup = BeautifulSoup(html, 'html.parser')
        container_selector = self.selectors.get('container')
        field_selectors = self.selectors['fields']

        try:
            if not container_selector:
                containers = [soup]
            else:
                containers = soup.select(container_selector)
        except SelectorSyntaxError as error:
            raise ValueError(f"Invalid container CSS selector: {container_selector}") from error

        if not containers:
            raise ValueError(f"No records matched container selector '{container_selector}'.")

        results = []
        for container in containers:
            record = {}
            for field_name, definition in field_selectors.items():
                if isinstance(definition, str):
                    selector = definition
                    attribute = "text"
                else:
                    selector = definition["selector"]
                    attribute = definition.get("attribute", "text")
                try:
                    element = container.select_one(selector)
                except SelectorSyntaxError as error:
                    raise ValueError(
                        f"Invalid CSS selector for field '{field_name}': {selector}"
                    ) from error

                if element is None:
                    record[field_name] = None
                elif attribute == "text":
                    record[field_name] = element.get_text(" ", strip=True)
                else:
                    record[field_name] = element.get(attribute)
            results.append(record)
            if max_records is not None and len(results) >= max_records:
                break

        return results

    async def run_multiple(self, max_records: int | None = None) -> list[ScrapedData]:
        """Fetch a page and return one structured result per matching record."""
        try:
            html = await self.fetch()
            records = await self.parse(html, max_records=max_records)
            return [
                ScrapedData(source_url=self.config.target_url, data=record)
                for record in records
            ]
        except Exception:
            logger.exception(f"GenericScraper failed for {self.config.target_url}")
            raise
