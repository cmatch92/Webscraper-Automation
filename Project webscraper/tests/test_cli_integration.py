import asyncio
import json
from pathlib import Path

from cli import main
from src.core.generic_scraper import GenericScraper
from src.core.models import ScrapedData


def test_cli_exports_records_without_live_requests(tmp_path, monkeypatch, capsys):
    config = tmp_path / "selectors.json"
    config.write_text(json.dumps({"fields": {"title": "h1"}}), encoding="utf-8")
    output = tmp_path / "nested" / "results.csv"

    monkeypatch.setattr("cli.validate_url", lambda url: True)

    async def fake_run_multiple(self, max_records):
        assert max_records == 20
        return [
            ScrapedData(
                source_url=self.config.target_url,
                data={"title": "Sample item"},
            )
        ]

    monkeypatch.setattr(GenericScraper, "run_multiple", fake_run_multiple)

    result = asyncio.run(
        main(
            [
                "--url",
                "https://public.example/items",
                "--config",
                str(config),
                "--output",
                str(output),
                "--max-records",
                "20",
            ]
        )
    )

    assert result == 0
    assert "Sample item" in output.read_text(encoding="utf-8-sig")
    assert "Exported 1 records" in capsys.readouterr().out


def test_cli_applies_record_limit_to_saved_demo_html(tmp_path, monkeypatch, capsys):
    project_dir = Path(__file__).resolve().parents[1]
    sample_html = (project_dir / "tests" / "fixtures" / "books_demo.html").read_text(
        encoding="utf-8"
    )
    config = project_dir / "config" / "books_toscrape.json"
    output = tmp_path / "books.csv"

    monkeypatch.setattr("cli.validate_url", lambda url: True)

    async def fake_fetch(self):
        return sample_html

    monkeypatch.setattr(GenericScraper, "fetch", fake_fetch)

    result = asyncio.run(
        main(
            [
                "--url",
                "https://books.toscrape.com/",
                "--config",
                str(config),
                "--output",
                str(output),
                "--max-records",
                "1",
            ]
        )
    )

    exported = output.read_text(encoding="utf-8-sig")
    assert result == 0
    assert "Demo Book One" in exported
    assert "Demo Book Two" not in exported
    assert "Exported 1 records" in capsys.readouterr().out


def test_cli_rejects_existing_output_before_network_or_config(
    tmp_path, monkeypatch, capsys
):
    output = tmp_path / "results.csv"
    output.write_text("keep", encoding="utf-8")

    result = asyncio.run(
        main(
            [
                "--url",
                "not-a-url",
                "--config",
                str(tmp_path / "missing.json"),
                "--output",
                str(output),
                "--max-records",
                "20",
            ]
        )
    )

    assert result == 1
    assert output.read_text(encoding="utf-8") == "keep"
    assert "already exists" in capsys.readouterr().err
