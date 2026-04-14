import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.antifraud.application.training import evaluate_model as em

JOBLIB_LOAD = "src.antifraud.application.training.evaluate_model.joblib.load"
LOAD_DATA = "src.antifraud.application.training.evaluate_model.load_and_preprocess_data"
EVAL_FN = "src.antifraud.application.training.evaluate_model.evaluate_model"
S3_DL = "src.antifraud.application.training.evaluate_model.s3_download"


def test_evaluate_missing():
    with (
        patch(S3_DL, side_effect=FileNotFoundError("not in s3")),
        pytest.raises(FileNotFoundError),
    ):
        em.evaluate("/nonexistent/m.joblib")


def test_evaluate_no_test(tmp_path, capsys):
    model_path = tmp_path / "m.joblib"
    model_path.write_text("x")
    with (
        patch(JOBLIB_LOAD, return_value=MagicMock()),
        patch(S3_DL),
        patch(
            "os.path.exists",
            side_effect=lambda p: str(p) == str(model_path),
        ),
    ):
        em.evaluate(str(model_path))
    assert "Skipping" in capsys.readouterr().out


def test_evaluate_with_test(tmp_path):
    model_path = tmp_path / "m.joblib"
    model_path.write_text("x")
    df = pd.DataFrame({"a": [1, 2], "Class": [0, 1]})
    with (
        patch(JOBLIB_LOAD, return_value=MagicMock()),
        patch(S3_DL),
        patch("os.path.exists", return_value=True),
        patch(LOAD_DATA, return_value=df),
        patch(EVAL_FN, return_value={"accuracy": 0.9}),
    ):
        em.evaluate(str(model_path))


def test_main(tmp_path, monkeypatch):
    model_path = tmp_path / "m.joblib"
    model_path.write_text("x")
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--model", str(model_path)])
    with (
        patch(JOBLIB_LOAD, return_value=MagicMock()),
        patch(S3_DL),
        patch(
            "os.path.exists",
            side_effect=lambda p: str(p) == str(model_path),
        ),
    ):
        em.main()
