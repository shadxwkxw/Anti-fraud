import logging

from fastapi import APIRouter, HTTPException, Query

from src.antifraud.config import config
from src.antifraud.domain.predictor import MODEL_PATH, get_artifacts, predict
from src.antifraud.infrastructure.storage.postgres import get_connection
from src.antifraud.interfaces.online.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    HistoryRecord,
    HistoryResponse,
    ModelInfoResponse,
    PredictionResponse,
    TransactionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Проверка состояния сервиса",
)
def health():
    """Возвращает статус сервиса: загружена ли модель, доступна ли БД."""
    model_ok = False
    try:
        get_artifacts()
        model_ok = True
    except Exception:
        pass

    db_status = "ok"
    try:
        conn = get_connection(connect_timeout=3)
        conn.close()
    except Exception:
        db_status = "unavailable"

    overall = "ok" if model_ok and db_status == "ok" else "degraded"
    return HealthResponse(status=overall, model_loaded=model_ok, database=db_status)


@router.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["predictions"],
    summary="Скоринг одной транзакции",
)
def fraud_predict(tx: TransactionRequest):
    """Принимает данные одной транзакции и возвращает вероятность мошенничества."""
    transaction = tx.to_domain()
    prediction = predict(transaction)
    return PredictionResponse.from_domain(prediction)


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["predictions"],
    summary="Скоринг нескольких транзакций",
)
def fraud_predict_batch(req: BatchPredictionRequest):
    """Принимает список транзакций (до 100) и возвращает предсказания для каждой."""
    results: list[PredictionResponse] = []
    for tx in req.transactions:
        transaction = tx.to_domain()
        prediction = predict(transaction)
        results.append(PredictionResponse.from_domain(prediction))

    fraud_count = sum(1 for r in results if r.is_fraud)
    return BatchPredictionResponse(
        predictions=results,
        total=len(results),
        fraud_count=fraud_count,
    )


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    tags=["model"],
    summary="Метаинформация о модели",
)
def model_info():
    """Возвращает тип модели, порог классификации, путь и количество фичей."""
    features_count = 0
    try:
        model, _ = get_artifacts()
        features_count = len(model.feature_names_in_)
    except Exception:
        pass

    return ModelInfoResponse(
        model_type=config["model"]["type"],
        threshold=config["model"]["threshold"],
        model_path=MODEL_PATH,
        features_count=features_count,
    )


@router.get(
    "/predictions/history",
    response_model=HistoryResponse,
    tags=["predictions"],
    summary="История предсказаний из БД",
)
def predictions_history(
    limit: int = Query(default=20, ge=1, le=200, description="Макс. кол-во записей"),
):
    """Возвращает последние предсказания, сохранённые в Postgres."""
    try:
        table = config["postgres"]["table"]
        conn = get_connection(connect_timeout=3)
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, timestamp, probability, is_fraud "
            f"FROM {table} ORDER BY id DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        records = [
            HistoryRecord(
                id=r[0],
                timestamp=str(r[1]) if r[1] else None,
                probability=float(r[2]),
                is_fraud=bool(r[3]),
            )
            for r in rows
        ]
        return HistoryResponse(records=records, total=len(records))
    except Exception as exc:
        logger.exception("Failed to fetch prediction history")
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
