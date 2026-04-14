import os
import sys
from unittest.mock import patch

from src.antifraud.application.training import register_model as rm

S3_DL = "src.antifraud.application.training.register_model.s3_download"
S3_UL = "src.antifraud.application.training.register_model.upload_model"


def test_register(tmp_path):
    src = tmp_path / "random_forest" / "model.joblib"
    src.parent.mkdir(parents=True)
    src.write_text("x")
    scaler = tmp_path / "random_forest" / "scaler.joblib"
    scaler.write_text("s")
    with patch(S3_UL):
        rm.register_model(str(src))


def test_register_downloads_from_s3(tmp_path):
    model_path = tmp_path / "rf" / "model.joblib"
    model_path.parent.mkdir(parents=True)

    def fake_download(_key, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("x")

    with (
        patch(S3_DL, side_effect=fake_download) as mock_dl,
        patch(S3_UL),
        patch("os.path.exists", return_value=False),
    ):
        rm.register_model(str(model_path))
    assert mock_dl.call_count == 2


def test_main(tmp_path, monkeypatch):
    src = tmp_path / "rf" / "model.joblib"
    src.parent.mkdir(parents=True)
    src.write_text("x")
    scaler = tmp_path / "rf" / "scaler.joblib"
    scaler.write_text("s")
    monkeypatch.setattr(sys, "argv", ["register.py", "--model", str(src)])
    with patch(S3_UL):
        rm.main()
