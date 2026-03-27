import json
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src.antifraud.config import config
from src.antifraud.domain.models import StoredPrediction


def get_connection():
    """Создает соединение с Postgres, используя параметры из конфига или переменных окружения."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", config["postgres"]["host"]),
        port=os.getenv("POSTGRES_PORT", config["postgres"]["port"]),
        database=os.getenv("POSTGRES_DB", config["postgres"]["database"]),
        user=os.getenv("POSTGRES_USER", config["postgres"]["user"]),
        password=os.getenv("POSTGRES_PASSWORD", config["postgres"]["password"]),
    )


def init_db():
    """Создает таблицу для предсказаний, если она не существует."""
    conn = get_connection()
    cur = conn.cursor()

    table_name = config["postgres"]["table"]

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data JSONB,
            probability FLOAT,
            is_fraud BOOLEAN
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print(f"Table {table_name} initialized in Postgres")


def save_prediction(prediction: StoredPrediction):
    """Сохраняет одно предсказание в Postgres."""
    conn = get_connection()
    cur = conn.cursor()

    table_name = config["postgres"]["table"]

    cur.execute(
        f"INSERT INTO {table_name} (data, probability, is_fraud) VALUES (%s, %s, %s)",
        (
            json.dumps(prediction.transaction_data),
            float(prediction.fraud_probability),
            bool(prediction.is_fraud),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def save_batch_predictions(df):
    """Сохраняет пакет предсказаний в Postgres."""
    conn = get_connection()
    cur = conn.cursor()

    table_name = config["postgres"]["table"]

    # Подготавливаем данные для пакетной вставки
    data_to_insert = []
    for _, row in df.iterrows():
        # Сохраняем все колонки кроме итоговых в JSONB
        row_data = row.drop(["fraud_probability", "is_fraud"]).to_dict()
        data_to_insert.append(
            (
                json.dumps(row_data),
                float(row["fraud_probability"]),
                bool(row["is_fraud"]),
            )
        )

    execute_values(
        cur,
        f"INSERT INTO {table_name} (data, probability, is_fraud) VALUES %s",
        data_to_insert,
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Saved {len(df)} predictions to Postgres table {table_name}")


def fetch_data_by_date(date):
    """Извлекает данные за конкретную дату из Postgres."""
    conn = get_connection()
    query = f"SELECT data FROM {config['postgres']['table']} WHERE date(timestamp) = %s"
    df = pd.read_sql(query, conn, params=(date,))
    conn.close()
    return df
