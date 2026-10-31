# Project Webscraper Automation
This project is a commercial-grade web scraping service.

## Project Structure
- `src/core`: Base classes and engine logic.
- `src/scrapers`: Site-specific scraping implementations.
- `src/utils`: Helpers for proxies, user-agents, and data cleaning.
- `data`: Storage for output files.
- `tests`: Automation tests to ensure scrapers haven't broken.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install`

## Development Goals
- Modular scraper design (Easy to add new clients).
- Anti-bot evasion (Randomized headers, proxy rotation).
- Structured output (Pydantic models).
