from pydantic import BaseModel, Field

from src.antifraud.domain.models import Prediction, Transaction


class TransactionRequest(BaseModel):
    """Pydantic-схема запроса — валидация входных данных API."""

    Time: float = Field(..., description="Время транзакции (секунды с начала датасета)")
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
    Amount: float = Field(..., ge=0, description="Сумма транзакции")

    model_config = {"json_schema_extra": {"examples": [{"Time": 406.0, "Amount": 125.0}]}}

    def to_domain(self) -> Transaction:
        """Преобразует API-запрос в доменную модель Transaction."""
        return Transaction(**self.model_dump())


class PredictionResponse(BaseModel):
    """Pydantic-схема ответа предсказания."""

    fraud_probability: float = Field(
        ..., ge=0, le=1, description="Вероятность мошенничества [0..1]"
    )
    is_fraud: bool = Field(..., description="Превышает ли вероятность порог")

    @classmethod
    def from_domain(cls, prediction: Prediction) -> "PredictionResponse":
        """Создаёт ответ API из доменной модели Prediction."""
        return cls(
            fraud_probability=prediction.fraud_probability,
            is_fraud=prediction.is_fraud,
        )


class BatchPredictionRequest(BaseModel):
    """Запрос на батчевое предсказание (несколько транзакций)."""

    transactions: list[TransactionRequest] = Field(
        ..., min_length=1, max_length=100, description="Список транзакций (макс. 100)"
    )


class BatchPredictionResponse(BaseModel):
    """Ответ на батчевое предсказание."""

    predictions: list[PredictionResponse]
    total: int = Field(..., description="Количество обработанных транзакций")
    fraud_count: int = Field(..., description="Количество подозрительных транзакций")


class ModelInfoResponse(BaseModel):
    """Pydantic-схема ответа о метаинформации модели."""

    model_type: str = Field(..., description="Тип модели (random_forest, etc.)")
    threshold: float = Field(..., description="Порог классификации")
    model_path: str = Field(..., description="Путь до файла модели")
    features_count: int = Field(0, description="Кол-во признаков модели")


class HealthResponse(BaseModel):
    """Ответ healthcheck-эндпоинта."""

    status: str = Field(..., description="Общий статус (ok / degraded)")
    model_loaded: bool = Field(..., description="Модель загружена в память")
    database: str = Field(..., description="Статус подключения к БД (ok / unavailable)")
