import csv
import json
from pathlib import Path
from typing import Sequence

from src.core.models import ScrapedData


def export_to_json(
    data: Sequence[ScrapedData], filename: str | Path, *, overwrite: bool = False
) -> None:
    """Export structured records as UTF-8 JSON."""
    output = [item.model_dump(mode="json") for item in data]
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", encoding="utf-8", newline="\n") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)
        file.write("\n")


def export_to_csv(
    data: Sequence[ScrapedData], filename: str | Path, *, overwrite: bool = False
) -> None:
    """Export extracted fields as a UTF-8 CSV file."""
    if not data:
        raise ValueError("Cannot export an empty result set.")

    all_keys: set[str] = set()
    for item in data:
        all_keys.update(item.data.keys())
    headers = sorted(all_keys)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for item in data:
            writer.writerow(item.data)
