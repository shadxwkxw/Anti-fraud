import sys
from unittest.mock import patch

import pandas as pd
import pytest

from src.antifraud.infrastructure.storage import save_predictions


def test_publish_missing():
    with pytest.raises(FileNotFoundError):
        save_predictions.publish_results("/nonexistent/x.csv")


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
