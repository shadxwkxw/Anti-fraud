import argparse
import os

import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from src.antifraud.application.training.utils import (
    evaluate_model,
    find_optimal_threshold,
    get_splits,
    load_and_preprocess_data,
)
from src.antifraud.config import config


def train_gb_model(input_path, output_path):
    """
    Обучает модель Gradient Boosting на данных из input_path.
    """
    # =========================
    # DATA PREPARATION
    # =========================
    print(f"Loading data from {input_path}...")
    df = load_and_preprocess_data(input_path)

    print("Splitting data...")
    X_train, X_test, y_train, y_test = get_splits(df)

    # =========================
    # MODEL: Gradient Boosting
    # =========================
    print("\nTraining Gradient Boosting...")
    gb_model = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=2, random_state=42
    )
    gb_model.fit(X_train, y_train)

    # =========================
    # EVALUATION
    # =========================
    print("\nModel Evaluation:")
    evaluate_model(gb_model, X_test, y_test)

    # Находим оптимальный порог
    threshold = find_optimal_threshold(gb_model, X_test, y_test)
    print(f"\nOptimal Threshold: {threshold:.4f}")

    # =========================
    # SAVE ARTIFACTS
    # =========================
    model_dir = os.path.dirname(output_path)
    if not model_dir:
        model_dir = "models/gradient_boosting"
    os.makedirs(model_dir, exist_ok=True)

    joblib.dump(gb_model, output_path)

    # Сохраняем скейлер
    scaler = StandardScaler()
    scaler.fit(X_train[["Amount"]])
    scaler_path = os.path.join(model_dir, "scaler.joblib")
    joblib.dump(scaler, scaler_path)

    print(f"\nGradient Boosting model and scaler saved to {model_dir}")


def main():
    """CLI entrypoint for Gradient Boosting training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=config["data"]["raw_path"])
    parser.add_argument("--output", default="models/gradient_boosting/model.joblib")
    args = parser.parse_args()

    train_gb_model(args.input, args.output)


if __name__ == "__main__":
    main()
