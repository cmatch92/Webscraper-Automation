# Webscraper Automation

[![Tests](https://github.com/cmatch92/Webscraper-Automation/actions/workflows/tests.yml/badge.svg)](https://github.com/cmatch92/Webscraper-Automation/actions/workflows/tests.yml)

A local tool that reads one public web page and saves the fields you choose as CSV or JSON. It fits small, approved data jobs, such as pulling a product list from a page the client is allowed to collect.

The demo below uses [Books to Scrape](https://books.toscrape.com/), a public sandbox site made for practicing scrapers.

## Features

- Selects records with a CSS `container` and pulls each field from inside that record
- Reads visible text, or an HTML attribute such as `href`, `src`, or `content`
- Writes UTF-8 CSV or JSON, and creates the output folder when it is missing
- Stops after `--max-records` so a job stays within the agreed size
- Accepts only public `http` and `https` URLs, and rejects local, private, and credentialed addresses
- Keeps an existing output file unless you pass `--force`
- Sends one request per run and refuses redirects

## Install

You need Python 3.10 or newer. From the repository root:

```bash
python -m pip install -r requirements.txt
```

For development and tests, also install the dev requirements:

```bash
python -m pip install -r requirements-dev.txt
```

## Usage

Copy [config/example_selectors.json](config/example_selectors.json) and edit the CSS selectors for the page you are allowed to read. A `container` selector matches one element per record. Each field selector runs inside that element.

Use a CSS selector string for visible text, or an object with `selector` and `attribute` for an HTML attribute. Attribute values are saved as they appear in the page. Relative links stay relative.

```json
{
  "container": "article.listing",
  "fields": {
    "title": "h2",
    "price": ".price",
    "listing_url": {
      "selector": "a.details",
      "attribute": "href"
    }
  }
}
```

Omit `container` when the page should produce a single record. Missing elements become empty CSV cells and JSON `null`. If a container is set and nothing matches, the run stops with an error.

Run the scraper with the page URL, the config file, an output path, and a record limit:

```bash
python main.py --url "https://permitted.example/listings" --config config/example_selectors.json --output data/results.csv --max-records 20
```

Use a `.json` path for JSON output. Add `--force` only when you mean to replace an existing file. `--timeout 30000` sets the request timeout in milliseconds (that value is the default). The `data/` folder is listed in `.gitignore`, so exported files stay on your machine.

| Flag | Required | Purpose |
| --- | --- | --- |
| `--url` | yes | Public HTTP or HTTPS page |
| `--config` | yes | JSON file of CSS selectors |
| `--output` | yes | Destination path ending in `.csv` or `.json` |
| `--max-records` | yes | Maximum number of records to save |
| `--timeout` | no | Request timeout in milliseconds (default 30000) |
| `--force` | no | Replace an existing output file |
| `--browser` | no | Rejected. Browser fetching is disabled |

### Books to Scrape demo

[config/books_toscrape.json](config/books_toscrape.json) is already set up for the Books to Scrape catalogue. This command saves the first 20 books to CSV:

```bash
python main.py --url "https://books.toscrape.com/" --config config/books_toscrape.json --output data/books.csv --max-records 20
```

Change the output name to `data/books.json` if you want JSON. That command fetches the live sandbox page. The automated tests use a saved copy of similar HTML and do not call the site.

Before quoting a client job, agree on the source URL, the exact fields, a modest record limit, the file format, and a short sample of the expected output. Deliver the file with a note that lists the fields, the record count, and any missing values. If the page layout changes later, treat that as separate work.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

The tests use saved HTML fixtures and mocked HTTP responses. They do not contact live websites. [GitHub Actions](.github/workflows/tests.yml) runs this same suite on every push and pull request.

## Project structure

```text
.
├── main.py                      # Command-line entry point
├── cli.py                       # Argument parsing, URL checks, and export
├── config/
│   ├── books_toscrape.json      # Selectors for the Books to Scrape demo
│   └── example_selectors.json   # Starter selector file
├── src/
│   ├── core/                    # Fetch, parse, and data models
│   └── utils/                   # CSV and JSON export
├── tests/                       # Pytest suite and saved HTML fixtures
├── requirements.txt
├── requirements-dev.txt
└── LICENSE
```

## Responsible scraping

Use this tool only on pages you are allowed to collect. Read the site's `robots.txt` and terms of use first, and confirm with the client that they may request the data.

Books to Scrape publishes a practice catalogue for this kind of demo. For a real page, test selector changes against a saved copy you are permitted to store.

Each run sends one request. The tool has no paging, scheduling, login, browser automation, or retry loop. It will not bypass CAPTCHAs, paywalls, access controls, or blocking. Redirects are rejected. The CLI checks that the URL uses HTTP or HTTPS and that the name resolves to public addresses, but DNS can change between that check and the connection. That check is not full protection against server-side request forgery, so keep this program on a machine you trust and do not expose it as a service that accepts URLs from strangers. If a site blocks the request, stop and ask about an official API or export.

## License

Released under the MIT License. See [LICENSE](LICENSE).
