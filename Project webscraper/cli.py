import argparse
import asyncio
import ipaddress
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit

from src.core.generic_scraper import GenericScraper
from src.core.models import ScraperConfig
from src.utils.exporter import export_to_csv, export_to_json


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def validate_url(url: str) -> bool:
    """Allow only public HTTP(S) URLs whose DNS answers are all globally routable."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.netloc
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            return False

        port = parsed.port
        normalized_host = hostname.rstrip(".").lower()
        if (
            normalized_host == "localhost"
            or normalized_host.endswith((".localhost", ".local", ".internal"))
        ):
            return False

        try:
            return ipaddress.ip_address(normalized_host).is_global
        except ValueError:
            pass

        addresses = socket.getaddrinfo(
            hostname,
            port or (443 if parsed.scheme.lower() == "https" else 80),
            type=socket.SOCK_STREAM,
        )
        if not addresses:
            return False

        return all(
            ipaddress.ip_address(address[4][0].split("%", 1)[0]).is_global
            for address in addresses
        )
    except (OSError, ValueError, UnicodeError):
        return False


def check_output_path(output_path: Path, force: bool) -> None:
    if output_path.suffix.lower() not in {".csv", ".json"}:
        raise ValueError("Output filename must end in .csv or .json.")
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Output file '{output_path}' already exists. Use --force to overwrite."
        )


def load_selectors(config_path: Path) -> dict:
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            selectors = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not load JSON config '{config_path}': {error}") from error

    if not isinstance(selectors, dict):
        raise ValueError("Config must be a JSON object containing selectors.")
    return selectors


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract permitted public webpage data to CSV or JSON."
    )
    parser.add_argument("--url", required=True, help="Public HTTP(S) page URL")
    parser.add_argument("--config", required=True, help="JSON file defining CSS selectors")
    parser.add_argument("--output", required=True, help="Output .csv or .json path")
    parser.add_argument(
        "--max-records",
        required=True,
        type=positive_int,
        help="Maximum number of records to collect",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Disabled: browser-based fetching is not supported",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Request timeout in milliseconds (default: 30000)",
    )
    args = parser.parse_args(argv)

    try:
        if args.browser:
            raise ValueError("Browser mode is disabled; use an authorized HTTP-accessible page.")

        output_path = Path(args.output)
        check_output_path(output_path, args.force)
        selectors = load_selectors(Path(args.config))
        if not validate_url(args.url):
            raise ValueError(
                "Invalid or forbidden URL. Only public HTTP(S) URLs are allowed."
            )

        config = ScraperConfig(
            target_url=args.url,
            timeout=args.timeout,
        )
        scraper = GenericScraper(config, selectors)

        print(f"Fetching {args.url}...")
        results = await scraper.run_multiple(max_records=args.max_records)
        if output_path.suffix.lower() == ".json":
            export_to_json(results, output_path, overwrite=args.force)
        else:
            export_to_csv(results, output_path, overwrite=args.force)

        print(f"Exported {len(results)} records to {output_path}.")
        return 0
    except (FileExistsError, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Scrape failed: {error}", file=sys.stderr)
        return 1


def cli_entrypoint() -> None:
    raise SystemExit(asyncio.run(main()))


if __name__ == "__main__":
    cli_entrypoint()
