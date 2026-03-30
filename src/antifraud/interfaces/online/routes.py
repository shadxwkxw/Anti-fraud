from fastapi import APIRouter

from src.antifraud.config import config
from src.antifraud.domain.predictor import MODEL_PATH, predict
from src.antifraud.interfaces.online.schemas import (
    ModelInfoResponse,
    PredictionResponse,
    TransactionRequest,
)

router = APIRouter()


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


@router.get("/model/info", response_model=ModelInfoResponse)
def model_info():
    return ModelInfoResponse(
        model_type=config["model"]["type"],
        threshold=config["model"]["threshold"],
        model_path=MODEL_PATH,
    )


@router.post("/predict", response_model=PredictionResponse)
def fraud_predict(tx: TransactionRequest):
    transaction = tx.to_domain()
    prediction = predict(transaction)

    return PredictionResponse.from_domain(prediction)
