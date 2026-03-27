from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Transaction:
    """Транзакция по кредитной карте — основная доменная сущность."""

    Time: float
    Amount: float
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

    def to_dict(self) -> dict:
        """Преобразует транзакцию в словарь для дальнейшей обработки."""
        return {
            "Time": self.Time,
            "Amount": self.Amount,
            **{f"V{i}": getattr(self, f"V{i}") for i in range(1, 29)},
        }


@dataclass
class TransactionFeatures:
    """Обогащённая транзакция с вычисленными признаками."""

    hour: float = 0.0
    is_night: int = 0
    recency: float = 0.0
    mean_amount: float = 0.0
    amount_ratio: float = 1.0
    tx_1h: float = 1.0
    tx_24h: float = 1.0
    tx_7d: float = 1.0


@dataclass
class Prediction:
    """Результат предсказания мошенничества."""

    fraud_probability: float
    is_fraud: bool
    threshold: float = 0.3

    @classmethod
    def from_probability(cls, probability: float, threshold: float = 0.3) -> "Prediction":
        return cls(
            fraud_probability=probability,
            is_fraud=probability > threshold,
            threshold=threshold,
        )


@dataclass
class StoredPrediction:
    """Сохранённое предсказание с метаданными."""

    id: int | None = None
    timestamp: datetime | None = None
    transaction_data: dict = field(default_factory=dict)
    fraud_probability: float = 0.0
    is_fraud: bool = False
