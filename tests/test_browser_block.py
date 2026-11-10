import pytest
import json
import subprocess
import sys
from pathlib import Path

def test_browser_mode_blocked(tmp_path):
    # Create a dummy config
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"fields": {"title": "title"}}))

    # Run CLI with --browser (should fail)
    result = subprocess.run(
        [sys.executable, "cli.py", "--url", "https://example.com",
         "--config", str(config_file), "--output", "out.csv",
         "--max-records", "20", "--browser"],
        capture_output=True, text=True
    )

    assert result.returncode != 0
    assert "Browser mode is disabled" in result.stderr
