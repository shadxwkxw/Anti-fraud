from pydantic import BaseModel

from src.antifraud.domain.models import Prediction, Transaction


class TransactionRequest(BaseModel):
    """Pydantic-схема запроса — валидация входных данных API."""

    Time: float
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float

    def to_domain(self) -> Transaction:
        """Преобразует API-запрос в доменную модель Transaction."""
        return Transaction(**self.model_dump())


class ModelInfoResponse(BaseModel):
    """Pydantic-схема ответа о метаинформации модели."""

    model_type: str
    threshold: float
    model_path: str


class PredictionResponse(BaseModel):
    """Pydantic-схема ответа API."""

    fraud_probability: float
    is_fraud: bool

    @classmethod
    def from_domain(cls, prediction: Prediction) -> "PredictionResponse":
        """Создаёт ответ API из доменной модели Prediction."""
        return cls(
            fraud_probability=prediction.fraud_probability,
            is_fraud=prediction.is_fraud,
        )
