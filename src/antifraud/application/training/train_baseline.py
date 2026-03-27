import argparse
import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.antifraud.application.training.utils import evaluate_model


def train_baseline(train_path, test_path, output_path):
    """
    Обучает базовую модель Logistic Regression.
    """
    # =========================
    # LOAD DATA
    # =========================
    print(f"Loading data from {train_path} and {test_path}...")
    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_path)

    print("Train shape:", train_df.shape)
    print("Test shape:", test_df.shape)

    # =========================
    # FEATURES / TARGET
    # =========================
    X_train = train_df.drop("Class", axis=1)
    y_train = train_df["Class"]

    X_test = test_df.drop("Class", axis=1)
    y_test = test_df["Class"]

    # =========================
    # SCALING
    # =========================
    scaler = StandardScaler()
    X_train["Amount"] = scaler.fit_transform(X_train[["Amount"]])
    X_test["Amount"] = scaler.transform(X_test[["Amount"]])

    # =========================
    # MODEL
    # =========================
    print("\nTraining Logistic Regression...")
    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    model.fit(X_train, y_train)

    # =========================
    # EVALUATION
    # =========================
    print("\nModel Evaluation:")
    evaluate_model(model, X_test, y_test)

    # =========================
    # SAVE ARTIFACTS
    # =========================
    model_dir = os.path.dirname(output_path)
    if not model_dir:
        model_dir = "models/baseline"
    os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, output_path)
    scaler_path = os.path.join(model_dir, "scaler.joblib")
    joblib.dump(scaler, scaler_path)

    print(f"\nBaseline model and scaler saved to {model_dir}")


def main():
    """CLI entrypoint for baseline model training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/splits/train.parquet")
    parser.add_argument("--test", default="data/splits/test.parquet")
    parser.add_argument("--output", default="models/baseline/model.joblib")
    args = parser.parse_args()

    train_baseline(args.train, args.test, args.output)


if __name__ == "__main__":
    main()
