from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class Transaction(BaseModel):
    """Транзакция по кредитной карте."""

    Time: float
    Amount: float = Field(ge=0)
    V1: float = 0.0
    V2: float = 0.0
    V3: float = 0.0
    V4: float = 0.0
    V5: float = 0.0
    V6: float = 0.0
    V7: float = 0.0
    V8: float = 0.0
    V9: float = 0.0
    V10: float = 0.0
    V11: float = 0.0
    V12: float = 0.0
    V13: float = 0.0
    V14: float = 0.0
    V15: float = 0.0
    V16: float = 0.0
    V17: float = 0.0
    V18: float = 0.0
    V19: float = 0.0
    V20: float = 0.0
    V21: float = 0.0
    V22: float = 0.0
    V23: float = 0.0
    V24: float = 0.0
    V25: float = 0.0
    V26: float = 0.0
    V27: float = 0.0
    V28: float = 0.0


class TransactionFeatures(BaseModel):
    """Обогащённая транзакция с вычисленными признаками."""

    hour: float = Field(default=0.0, ge=0, le=23)
    is_night: int = Field(default=0, ge=0, le=1)
    recency: float = 0.0
    mean_amount: float = 0.0
    amount_ratio: float = 1.0
    tx_1h: float = Field(default=1.0, ge=0)
    tx_24h: float = Field(default=1.0, ge=0)
    tx_7d: float = Field(default=1.0, ge=0)


class Prediction(BaseModel):
    """Результат предсказания мошенничества."""

    fraud_probability: float = Field(ge=0.0, le=1.0)
    is_fraud: bool
    threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def compute_is_fraud(cls, values: dict) -> dict:
        if "fraud_probability" in values and "is_fraud" not in values:
            values["is_fraud"] = values["fraud_probability"] > values.get("threshold", 0.3)
        return values


class StoredPrediction(BaseModel):
    """Сохранённое предсказание с метаданными."""

    id: int | None = None
    timestamp: datetime | None = None
    transaction_data: dict = Field(default_factory=dict)
    fraud_probability: float = Field(ge=0.0, le=1.0, default=0.0)
    is_fraud: bool = False