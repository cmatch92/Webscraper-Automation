# Public-page data extraction

This project is a local, single-page scraper for small, client-approved jobs. It
fetches one public HTTP(S) page per run and exports selected fields to CSV or JSON.
It is a starter tool, not a hosted scraping service or a promise that a website's
layout will stay unchanged.

## Setup

From the project directory:

```powershell
python -m pip install -r requirements.txt
```

No browser installation is needed. Browser-based scraping is disabled.
For local development and tests, also install `requirements-dev.txt`.

## Configure selectors

Copy [config/example_selectors.json](config/example_selectors.json) and edit its
CSS selectors for the agreed page. A `container` selects one element per record;
each field selector is evaluated inside each selected container.

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

Use a regular CSS selector string for visible text, or an object with `selector`
and `attribute` to extract an HTML attribute such as `href`, `src`, or `content`.
Attribute values are exported as found in the page; relative links are not
automatically converted to absolute URLs.
Omit `container` for a single record from the whole page. Missing elements become
empty CSV cells / JSON `null`; no matching containers is an error.

## Run

```powershell
python main.py --url "https://permitted.example/listings" --config config/example_selectors.json --output data/results.csv
```

Use `.json` instead of `.csv` for JSON output. Existing files are protected; add
`--force` only when intentionally replacing one. Optional `--timeout 30000` sets
the request timeout in milliseconds. Output folders are created as needed.

## Scope and client expectations

- Get client confirmation that they may collect the specified data, and check the
  site's terms, access rules, and applicable privacy requirements before running.
- Agree on the source URL, exact fields, a modest record limit, file format, and
  acceptance example before quoting a job.
- Deliver the output file and a brief note describing the fields, record count,
  and any missing values. Quote site changes or recurring work separately.
- Test selector changes against a saved, permitted HTML sample. Automated tests
  make no live website requests.

This tool does one request per run. It has no automatic pacing, pagination,
scheduling, login support, browser support, or retry behavior. It does not bypass
CAPTCHAs, paywalls, access controls, or anti-bot measures. Redirects are rejected.
The CLI checks that the initial URL uses HTTP(S) and resolves to globally routable
addresses, but DNS can change between validation and connection; this is not
complete SSRF protection and the tool should not be exposed as a service that
accepts untrusted URLs. Stop if the site blocks the request and ask the client
about an authorized API or export.

## Example service listing

> I will extract a clearly scoped set of publicly accessible fields from one
> client-approved webpage and deliver a tidy CSV or JSON file. Please message me
> first with the URL, fields, approximate number of records, and confirmation
> that you are authorized to request the data. Login-only, paywalled, blocked,
> or prohibited sources are out of scope.

Keep package limits and delivery dates specific to the site after checking it;
do not guarantee uninterrupted operation if the site changes.

## Run checks

```powershell
python -m pytest
```
