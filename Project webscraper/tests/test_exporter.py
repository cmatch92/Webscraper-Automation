import csv
import json

import pytest

from src.core.models import ScrapedData
from src.utils.exporter import export_to_csv, export_to_json


@pytest.fixture
def records():
    return [
        ScrapedData(
            source_url="https://example.test/items",
            data={"title": "First", "price": "$10"},
        ),
        ScrapedData(
            source_url="https://example.test/items",
            data={"title": "Second", "link": "/second"},
        ),
    ]


def test_csv_export_creates_parent_and_unions_columns(tmp_path, records):
    output = tmp_path / "nested" / "results.csv"

    export_to_csv(records, output)

    with output.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    assert set(rows[0]) == {"link", "price", "title"}
    assert rows[0] == {"link": "", "price": "$10", "title": "First"}
    assert rows[1] == {"link": "/second", "price": "", "title": "Second"}


def test_json_export_is_valid_and_includes_iso_timestamp(tmp_path, records):
    output = tmp_path / "results.json"

    export_to_json(records, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 2
    assert payload[0]["data"]["title"] == "First"
    assert payload[0]["timestamp"].endswith("Z")


def test_export_does_not_overwrite_without_opt_in(tmp_path, records):
    output = tmp_path / "results.json"
    output.write_text("preserve", encoding="utf-8")

    with pytest.raises(FileExistsError):
        export_to_json(records, output)

    assert output.read_text(encoding="utf-8") == "preserve"


def test_csv_export_rejects_empty_results(tmp_path):
    with pytest.raises(ValueError, match="empty result"):
        export_to_csv([], tmp_path / "empty.csv")
