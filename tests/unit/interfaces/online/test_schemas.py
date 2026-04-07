from src.antifraud.domain.models import Prediction, Transaction
from src.antifraud.interfaces.online.schemas import (
    ModelInfoResponse,
    PredictionResponse,
    TransactionRequest,
)


def _tx_payload():
    d = {"Time": 0.0, "Amount": 10.0}
    for i in range(1, 29):
        d[f"V{i}"] = 0.1 * i
    return d


def test_transaction_request_to_domain():
    req = TransactionRequest(**_tx_payload())
    domain = req.to_domain()
    assert isinstance(domain, Transaction)
    assert domain.Amount == 10.0
    assert domain.V5 == 0.5


def test_prediction_response_from_domain():
    pred = Prediction(fraud_probability=0.9, threshold=0.3)
    resp = PredictionResponse.from_domain(pred)
    assert resp.fraud_probability == 0.9
    assert resp.is_fraud is True


def test_prediction_response_not_fraud():
    pred = Prediction(fraud_probability=0.1, threshold=0.3)
    resp = PredictionResponse.from_domain(pred)
    assert resp.is_fraud is False


def test_model_info_response():
    r = ModelInfoResponse(model_type="rf", threshold=0.5, model_path="/tmp/m")
    assert r.model_type == "rf"
    assert r.threshold == 0.5
