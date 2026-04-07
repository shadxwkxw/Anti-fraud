import sys
from unittest.mock import patch

from src.antifraud.infrastructure.data_processing import extract


def test_extract_missing_source(tmp_path, capsys):
    with patch.dict(extract.config, {"data": {"raw_path": str(tmp_path / "none.csv")}}):
        extract.extract_data("2024-01-01", str(tmp_path / "out.csv"))
    assert "not found" in capsys.readouterr().out


def test_extract_copies(tmp_path):
    src = tmp_path / "raw.csv"
    src.write_text("a,b\n1,2\n")
    dst = tmp_path / "sub" / "out.csv"
    with patch.dict(extract.config, {"data": {"raw_path": str(src)}}):
        extract.extract_data("2024-01-01", str(dst))
    assert dst.exists()


def test_extract_same_path(tmp_path, capsys):
    src = tmp_path / "raw.csv"
    src.write_text("a\n1\n")
    with patch.dict(extract.config, {"data": {"raw_path": str(src)}}):
        extract.extract_data("2024-01-01", str(src))
    assert "Skipping" in capsys.readouterr().out


def test_extract_main(tmp_path, monkeypatch):
    src = tmp_path / "raw.csv"
    src.write_text("a\n1\n")
    dst = tmp_path / "out.csv"
    monkeypatch.setattr(sys, "argv", ["extract.py", "--date", "2024-01-01", "--output", str(dst)])
    with patch.dict(extract.config, {"data": {"raw_path": str(src)}}):
        extract.main()
    assert dst.exists()
