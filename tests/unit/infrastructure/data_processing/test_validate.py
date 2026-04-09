import sys
from unittest.mock import patch

import pandas as pd
import pytest

from src.antifraud.infrastructure.data_processing import validate

S3_DOWNLOAD = "src.antifraud.infrastructure.data_processing.validate.s3_download"


def _write_csv(tmp_path, df, name="d.csv"):
    p = tmp_path / name
    df.to_csv(p, index=False)
    return str(p)


def test_validate_ok(tmp_path, capsys):
    path = _write_csv(tmp_path, pd.DataFrame({"Time": [0, 1], "Amount": [1.0, 2.0]}))
    validate.validate_data(path)
    out = capsys.readouterr().out
    assert "Validation successful" in out


def test_validate_with_nulls(tmp_path, capsys):
    path = _write_csv(tmp_path, pd.DataFrame({"Time": [0, 1], "Amount": [1.0, None]}))
    validate.validate_data(path)
    assert "null values" in capsys.readouterr().out


def test_validate_missing_col(tmp_path):
    path = _write_csv(tmp_path, pd.DataFrame({"Time": [0, 1]}))
    with pytest.raises(ValueError):
        validate.validate_data(path)


def test_validate_missing_file():
    with patch(S3_DOWNLOAD, side_effect=FileNotFoundError("not in S3")):
        with pytest.raises(FileNotFoundError):
            validate.validate_data("/tmp/nonexistent_test_abc.csv")


def test_validate_main(tmp_path, monkeypatch):
    path = _write_csv(tmp_path, pd.DataFrame({"Time": [0], "Amount": [1.0]}))
    monkeypatch.setattr(sys, "argv", ["validate.py", "--input", path])
    validate.main()
