import argparse
import os

from src.antifraud.infrastructure.storage.s3 import upload_model
from src.antifraud.infrastructure.storage.s3_io import s3_download


def register_model(model_path):
    """
    Регистрация модели как основной (PROD).
    Скачивает модель из S3 (если нет локально) и загружает как production-артефакт.
    """
    if not os.path.exists(model_path):
        s3_download("random_forest/model.joblib", model_path)

    # Загружаем scaler рядом с моделью
    model_dir = os.path.dirname(model_path)
    scaler_path = os.path.join(model_dir, "scaler.joblib")
    if not os.path.exists(scaler_path):
        s3_download("random_forest/scaler.joblib", scaler_path)

    # Регистрируем как production в S3
    upload_model(model_path, s3_key="random_forest/model.joblib")
    upload_model(scaler_path, s3_key="random_forest/scaler.joblib")
    print(f"Model {model_path} registered as production model in S3")


def main():
    """CLI entrypoint for production model registration."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    register_model(args.model)


if __name__ == "__main__":
    main()
