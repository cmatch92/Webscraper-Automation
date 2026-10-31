import json
import socket
import subprocess
import sys

import pytest

from cli import check_output_path, validate_url
from src.core.models import ScrapedData
from src.utils.exporter import export_to_csv


def _dns_result(address: str, port: int = 443):
    return (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))


def test_url_validation(monkeypatch):
    def resolve(host, port, **kwargs):
        return [_dns_result("93.184.216.34", port)]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)

    assert validate_url("https://public.example") is True
    assert validate_url("http://public.example") is True
    assert validate_url("ftp://public.example") is False
    assert validate_url("file:///etc/passwd") is False
    assert validate_url("https://localhost") is False
    assert validate_url("https://sub.localhost") is False
    assert validate_url("http://127.0.0.1") is False
    assert validate_url("http://192.168.1.1") is False
    assert validate_url("http://10.0.0.1") is False
    assert validate_url("http://169.254.169.254") is False
    assert validate_url("https://user:pass@public.example") is False
    assert validate_url("not-a-url") is False
    assert validate_url("") is False


def test_dns_resolution_rejects_non_public_answers(monkeypatch):
    def resolve(host, port, **kwargs):
        answers = {
            "mixed.example": ["93.184.216.34", "10.0.0.1"],
            "private.example": ["192.168.1.1"],
            "public.example": ["93.184.216.34"],
        }
        return [_dns_result(address, port) for address in answers[host]]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)

    assert validate_url("https://mixed.example") is False
    assert validate_url("https://private.example") is False
    assert validate_url("https://public.example") is True


def test_dns_resolution_failure_is_rejected(monkeypatch):
    def fail_resolution(host, port, **kwargs):
        raise socket.gaierror("name resolution failed")

    monkeypatch.setattr(socket, "getaddrinfo", fail_resolution)
    assert validate_url("https://unresolved.example") is False


def test_output_path_rejects_existing_file_without_force(tmp_path):
    output = tmp_path / "results.csv"
    output.write_text("keep this data", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Use --force"):
        check_output_path(output, force=False)
    assert output.read_text(encoding="utf-8") == "keep this data"


def test_output_path_accepts_force_and_supported_extensions(tmp_path):
    output = tmp_path / "results.csv"
    output.write_text("old", encoding="utf-8")
    check_output_path(output, force=True)
    with pytest.raises(ValueError, match="must end"):
        check_output_path(tmp_path / "results.txt", force=False)


def test_force_export_replaces_existing_file(tmp_path):
    output = tmp_path / "results.csv"
    output.write_text("old", encoding="utf-8")
    records = [
        ScrapedData(source_url="https://public.example", data={"title": "New item"})
    ]

    export_to_csv(records, output, overwrite=True)

    assert "New item" in output.read_text(encoding="utf-8-sig")


def test_browser_option_is_rejected(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"fields": {"title": "h1"}}), encoding="utf-8")
    output = tmp_path / "results.csv"

    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--url",
            "https://public.example",
            "--config",
            str(config),
            "--output",
            str(output),
            "--max-records",
            "20",
            "--browser",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Browser mode is disabled" in result.stderr
