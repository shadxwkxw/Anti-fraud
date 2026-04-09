import argparse
import os

from src.antifraud.application.batch_predict import run_batch
from src.antifraud.config import config
from src.antifraud.infrastructure.storage.s3 import download_model


def ensure_models():
    """Загружает модель и скейлер из S3, если они отсутствуют локально."""
    model_dir = config["storage"]["model_dir"]
    model_type = config["model"]["type"]

    local_dir = os.path.join(model_dir, model_type)
    os.makedirs(local_dir, exist_ok=True)

    for filename in ("model.joblib", "scaler.joblib"):
        local_path = os.path.join(local_dir, filename)
        if not os.path.exists(local_path):
            s3_key = f"{model_type}/{filename}"
            print(f"Downloading {s3_key} from S3...")
            download_model(s3_key, local_path)


def ensure_dataset(local_path: str) -> None:
    """Загружает датасет из S3, если он отсутствует локально."""
    if os.path.exists(local_path):
        return

    output_dir = os.path.dirname(local_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading dataset {local_path} from S3...")
    download_model(local_path, local_path)


def main():
    """CLI entrypoint for batch service."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default=config["data"]["raw_path"])
    parser.add_argument("output", nargs="?", default="artifacts/batch_predictions.csv")
    args = parser.parse_args()

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    ensure_models()
    ensure_dataset(args.input)
    run_batch(args.input, args.output)
    print("Batch inference finished via service entrypoint")


if __name__ == "__main__":
    main()
