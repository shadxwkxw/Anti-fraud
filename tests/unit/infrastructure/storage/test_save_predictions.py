import sys
from unittest.mock import patch

import pandas as pd
import pytest

from src.antifraud.infrastructure.storage import save_predictions

S3_DOWNLOAD = "src.antifraud.infrastructure.storage.save_predictions.s3_download"


def test_publish_missing():
    with patch(S3_DOWNLOAD, side_effect=FileNotFoundError("not in S3")):
        with pytest.raises(FileNotFoundError):
            save_predictions.publish_results("/tmp/nonexistent_test_abc.csv")


def test_publish_ok(tmp_path):
    p = tmp_path / "p.csv"
    pd.DataFrame(
        {"Time": [0], "Amount": [1.0], "fraud_probability": [0.9], "is_fraud": [True]}
    ).to_csv(p, index=False)
    with (
        patch("src.antifraud.infrastructure.storage.save_predictions.init_db"),
        patch("src.antifraud.infrastructure.storage.save_predictions.save_batch_predictions") as s,
    ):
        save_predictions.publish_results(str(p))
    s.assert_called_once()


def test_main(tmp_path, monkeypatch):
    p = tmp_path / "p.csv"
    pd.DataFrame(
        {"Time": [0], "Amount": [1.0], "fraud_probability": [0.9], "is_fraud": [True]}
    ).to_csv(p, index=False)
    monkeypatch.setattr(sys, "argv", ["save.py", "--input", str(p)])
    with (
        patch("src.antifraud.infrastructure.storage.save_predictions.init_db"),
        patch("src.antifraud.infrastructure.storage.save_predictions.save_batch_predictions"),
    ):
        save_predictions.main()
