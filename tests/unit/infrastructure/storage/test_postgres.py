from unittest.mock import MagicMock, patch

import pandas as pd

from src.antifraud.domain.models import StoredPrediction
from src.antifraud.infrastructure.storage import postgres


def _mock_conn():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


def test_get_connection():
    with patch("src.antifraud.infrastructure.storage.postgres.psycopg2") as p:
        postgres.get_connection()
        p.connect.assert_called_once()


def test_init_db():
    conn, cur = _mock_conn()
    with patch("src.antifraud.infrastructure.storage.postgres.get_connection", return_value=conn):
        postgres.init_db()
    cur.execute.assert_called()
    conn.commit.assert_called()


def test_save_prediction():
    conn, cur = _mock_conn()
    with patch("src.antifraud.infrastructure.storage.postgres.get_connection", return_value=conn):
        postgres.save_prediction(
            StoredPrediction(transaction_data={"a": 1}, fraud_probability=0.9, is_fraud=True)
        )
    cur.execute.assert_called()
    conn.commit.assert_called()


def test_save_batch_predictions():
    conn, _ = _mock_conn()
    df = pd.DataFrame(
        {
            "Time": [0, 1, 2],
            "Amount": [1.0, 2.0, 3.0],
            "fraud_probability": [0.1, 0.9, 0.5],
            "is_fraud": [False, True, False],
        }
    )
    with (
        patch("src.antifraud.infrastructure.storage.postgres.get_connection", return_value=conn),
        patch("src.antifraud.infrastructure.storage.postgres.execute_values") as ev,
    ):
        postgres.save_batch_predictions(df, execution_date="2024-01-01", chunk_size=2)
    assert ev.called


def test_fetch_data_by_date():
    conn = MagicMock()
    with (
        patch("src.antifraud.infrastructure.storage.postgres.get_connection", return_value=conn),
        patch(
            "src.antifraud.infrastructure.storage.postgres.pd.read_sql",
            return_value=pd.DataFrame({"data": [{}]}),
        ),
    ):
        out = postgres.fetch_data_by_date("2024-01-01")
    assert len(out) == 1
