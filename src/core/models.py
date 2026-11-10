from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

class ScrapedData(BaseModel):
    """Standardized output format for all scrapers."""
    source_url: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ScraperConfig(BaseModel):
    """Configuration for a specific scraping task."""
    target_url: str
    use_browser: bool = False
    timeout: int = Field(default=30000, gt=0, description="Request timeout in milliseconds")
    headers: Dict[str, str] = Field(default_factory=dict)
