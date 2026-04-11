from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.antifraud.domain.models import Prediction
from src.antifraud.interfaces.online.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

PG_CONN = "src.antifraud.interfaces.online.routes.get_connection"


def _payload():
    d = {"Time": 0.0, "Amount": 10.0}
    for i in range(1, 29):
        d[f"V{i}"] = 0.0
    return d


def test_health_ok():
    mock_model = MagicMock()
    with (
        patch(
            "src.antifraud.interfaces.online.routes.get_artifacts",
            return_value=(mock_model, None),
        ),
        patch(PG_CONN, return_value=MagicMock()),
    ):
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["database"] == "ok"


def test_health_degraded_no_model():
    with (
        patch(
            "src.antifraud.interfaces.online.routes.get_artifacts",
            side_effect=FileNotFoundError,
        ),
        patch(PG_CONN, return_value=MagicMock()),
    ):
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degraded"
    assert r.json()["model_loaded"] is False


def test_model_info():
    mock_model = MagicMock()
    mock_model.feature_names_in_ = [f"V{i}" for i in range(1, 29)]
    with patch(
        "src.antifraud.interfaces.online.routes.get_artifacts",
        return_value=(mock_model, None),
    ):
        r = client.get("/model/info")
    assert r.status_code == 200
    body = r.json()
    assert "model_type" in body
    assert "threshold" in body
    assert body["features_count"] == 28


def test_predict():
    fake = Prediction(fraud_probability=0.8, threshold=0.3)
    with patch("src.antifraud.interfaces.online.routes.predict", return_value=fake):
        r = client.post("/predict", json=_payload())
    assert r.status_code == 200
    body = r.json()
    assert body["fraud_probability"] == 0.8
    assert body["is_fraud"] is True


def test_predict_batch():
    fake = Prediction(fraud_probability=0.8, threshold=0.3)
    with patch("src.antifraud.interfaces.online.routes.predict", return_value=fake):
        r = client.post("/predict/batch", json={"transactions": [_payload(), _payload()]})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["fraud_count"] == 2
    assert len(body["predictions"]) == 2


def test_predict_batch_empty():
    r = client.post("/predict/batch", json={"transactions": []})
    assert r.status_code == 422


def test_predictions_history():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = [
        (1, "2024-01-01 12:00:00", 0.95, True),
        (2, "2024-01-01 12:01:00", 0.10, False),
    ]
    with patch(PG_CONN, return_value=mock_conn):
        r = client.get("/predictions/history?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["records"][0]["probability"] == 0.95
    assert body["records"][0]["is_fraud"] is True


def test_predictions_history_db_unavailable():
    with patch(PG_CONN, side_effect=ConnectionError("no db")):
        r = client.get("/predictions/history")
    assert r.status_code == 503
