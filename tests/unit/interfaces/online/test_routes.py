from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.antifraud.domain.models import Prediction
from src.antifraud.interfaces.online.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _payload():
    d = {"Time": 0.0, "Amount": 10.0}
    for i in range(1, 29):
        d[f"V{i}"] = 0.0
    return d


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_model_info():
    r = client.get("/model/info")
    assert r.status_code == 200
    body = r.json()
    assert "model_type" in body
    assert "threshold" in body


def test_predict():
    fake = Prediction(fraud_probability=0.8, threshold=0.3)
    with patch("src.antifraud.interfaces.online.routes.predict", return_value=fake):
        r = client.post("/predict", json=_payload())
    assert r.status_code == 200
    body = r.json()
    assert body["fraud_probability"] == 0.8
    assert body["is_fraud"] is True
