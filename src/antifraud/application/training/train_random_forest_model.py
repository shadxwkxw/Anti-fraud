import argparse
import os

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from src.antifraud.application.training.utils import (
    evaluate_model,
    find_optimal_threshold,
    load_and_preprocess_data,
)
from src.antifraud.config import config
from src.antifraud.infrastructure.storage.s3 import upload_model
from src.antifraud.infrastructure.storage.s3_io import s3_download


def train_model(input_path, output_path):
    """
    Обучает модел�� Random Forest на данных из input_path.
    """
    # =========================
    # DATA PREPARATION
    # =========================
    if not os.path.exists(input_path):
        s3_download(os.path.basename(input_path), input_path)

    print(f"Loading data from {input_path}...")
    train_df = load_and_preprocess_data(input_path)

    test_path = "data/splits/test.parquet"
    if not os.path.exists(test_path):
        s3_download("test.parquet", test_path)

    print(f"Loading test data from {test_path}...")
    test_df = load_and_preprocess_data(test_path)

    X_train = train_df.drop("Class", axis=1)
    y_train = train_df["Class"]

    X_test = test_df.drop("Class", axis=1)
    y_test = test_df["Class"]

    # =========================
    # MODEL TRAINING
    # =========================
    print("\nTraining Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # =========================
    # EVALUATION
    # =========================
    print("\nModel Evaluation:")
    evaluate_model(model, X_test, y_test)

    # Находим оптимальный порог
    threshold = find_optimal_threshold(model, X_test, y_test)
    print(f"\nOptimal Threshold: {threshold:.4f}")

    # =========================
    # SAVE ARTIFACTS
    # =========================
    model_dir = os.path.dirname(output_path)
    if not model_dir:
        model_dir = "models/random_forest"
    os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, output_path)

    # Сохраняем скейлер
    scaler = StandardScaler()
    scaler.fit(X_train[["Amount"]])
    scaler_path = os.path.join(model_dir, "scaler.joblib")
    joblib.dump(scaler, scaler_path)

    print(f"\nRandom Forest model and scaler saved to {model_dir}")

    # =========================
    # UPLOAD TO S3
    # =========================
    print("\nUploading model to S3...")
    upload_model(output_path, s3_key="random_forest/model.joblib")
    upload_model(scaler_path, s3_key="random_forest/scaler.joblib")


def main():
    """CLI entrypoint for Random Forest training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=config["data"]["raw_path"])
    parser.add_argument("--output", default="models/random_forest/model.joblib")
    args = parser.parse_args()

    train_model(args.input, args.output)


if __name__ == "__main__":
    main()
