import os
import sys

from src.antifraud.application.training import register_model as rm


def test_register(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "m.joblib"
    src.write_text("x")
    rm.register_model(str(src))
    assert os.path.exists("models/random_forest/model.joblib")


def test_main(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "m.joblib"
    src.write_text("x")
    monkeypatch.setattr(sys, "argv", ["register.py", "--model", str(src)])
    rm.main()
