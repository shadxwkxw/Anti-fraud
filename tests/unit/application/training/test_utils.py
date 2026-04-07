from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from src.antifraud.application.training import utils


def _df(n=20):
    rng = np.random.default_rng(0)
    d = {"Time": np.arange(n) * 100.0, "Amount": rng.random(n) * 10}
    for i in range(1, 29):
        d[f"V{i}"] = rng.random(n)
    d["Class"] = [0] * (n - 2) + [1, 1]
    return pd.DataFrame(d)


def test_load_and_preprocess_csv(tmp_path):
    p = tmp_path / "d.csv"
    _df().to_csv(p, index=False)
    out = utils.load_and_preprocess_data(str(p))
    assert "hour" in out.columns
    assert "is_night" in out.columns
    assert "recency" in out.columns


def test_load_and_preprocess_parquet(tmp_path):
    p = tmp_path / "d.parquet"
    _df().to_parquet(p, index=False)
    out = utils.load_and_preprocess_data(str(p))
    assert len(out) > 0


def test_get_splits():
    df = _df(40)
    Xtr, Xte, ytr, yte = utils.get_splits(df)
    assert len(Xtr) + len(Xte) == 40
    assert len(ytr) + len(yte) == 40


def test_evaluate_model():
    model = MagicMock()
    model.predict.return_value = np.array([0, 1, 0, 1])
    y = pd.Series([0, 1, 0, 0])
    res = utils.evaluate_model(model, pd.DataFrame({"a": [1, 2, 3, 4]}), y)
    assert isinstance(res, dict)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_find_optimal_threshold_none():
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.9, 0.1], [0.8, 0.2], [0.7, 0.3]])
    y = pd.Series([0, 0, 0])
    out = utils.find_optimal_threshold(
        model, pd.DataFrame({"a": [1, 2, 3]}), y, target_precision=0.99
    )
    assert out == 0.5


def test_find_optimal_threshold_ok():
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.1, 0.9], [0.2, 0.8], [0.8, 0.2], [0.9, 0.1]])
    y = pd.Series([1, 1, 0, 0])
    out = utils.find_optimal_threshold(
        model, pd.DataFrame({"a": [1, 2, 3, 4]}), y, target_precision=0.5
    )
    assert 0.0 <= out <= 1.0
