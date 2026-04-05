import os
from functools import lru_cache

import joblib
import pandas as pd

from src.antifraud.config import config
from src.antifraud.domain.models import Prediction, Transaction

MODEL_DIR = config["storage"]["model_dir"]
MODEL_TYPE = config["model"]["type"]

MODEL_PATH = os.path.join(MODEL_DIR, MODEL_TYPE, "model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, MODEL_TYPE, "scaler.joblib")


@lru_cache(maxsize=1)
def get_artifacts():
    """Loads model artifacts lazily to simplify imports and tests."""
    return joblib.load(MODEL_PATH), joblib.load(SCALER_PATH)


def preprocess_single_tx(transaction: Transaction):
    """Применяет те же преобразования, что и при обучении, к одной транзакции."""
    model, scaler = get_artifacts()
    df = pd.DataFrame([transaction.model_dump()])

    # Feature Engineering (соответствует utils.py)
    df["recency"] = 0.0
    df["tx_1h"] = 1.0
    df["tx_24h"] = 1.0
    df["tx_7d"] = 1.0
    df["mean_amount"] = df["Amount"]
    df["amount_ratio"] = 1.0

    df["hour"] = (df["Time"] // 3600) % 24
    df["is_night"] = df["hour"].between(1, 5).astype(int)

    # Масштабирование Amount
    df["Amount"] = scaler.transform(df[["Amount"]])

    # Оставляем только те колонки, на которых училась модель
    expected_features = model.feature_names_in_
    df = df[expected_features]

    return df


def predict(transaction: Transaction) -> Prediction:
    """Выполняет предсказание для одиночной транзакции."""
    model, _ = get_artifacts()
    df = preprocess_single_tx(transaction)
    prob = model.predict_proba(df)[0][1]
    threshold = config["model"]["threshold"]
    return Prediction(fraud_probability=float(prob), threshold=threshold)
