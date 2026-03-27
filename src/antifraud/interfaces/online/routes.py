from fastapi import APIRouter
from prometheus_client import Counter

from src.antifraud.domain.predictor import predict
from src.antifraud.interfaces.online.schemas import PredictionResponse, TransactionRequest

router = APIRouter()

# metrics
predictions_total = Counter(
    "fraud_predictions_total",
    "Total number of predictions",
)

fraud_predictions = Counter(
    "fraud_detected_total",
    "Total fraud predictions",
)


@router.get("/")
def root():
    return {
        "message": "Anti-fraud ML System API",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/predict", response_model=PredictionResponse)
def fraud_predict(tx: TransactionRequest):
    transaction = tx.to_domain()
    prediction = predict(transaction)

    predictions_total.inc()

    if prediction.is_fraud:
        fraud_predictions.inc()

    return PredictionResponse.from_domain(prediction)
