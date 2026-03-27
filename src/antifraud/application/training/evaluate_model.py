import argparse
import os

import joblib

from src.antifraud.application.training.utils import evaluate_model, load_and_preprocess_data


def evaluate(model_path):
    """
    Оценка модели перед регистрацией.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model {model_path} not found")

    model = joblib.load(model_path)

    # В реальности здесь загружается валидационный сет
    test_path = "data/splits/test.parquet"
    if os.path.exists(test_path):
        df_test = load_and_preprocess_data(test_path)
        X_test = df_test.drop("Class", axis=1)
        y_test = df_test["Class"]

        metrics = evaluate_model(model, X_test, y_test)
        print(f"Evaluation metrics: {metrics}")
    else:
        print("Skipping detailed evaluation: test split not found")


def main():
    """CLI entrypoint for model evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    evaluate(args.model)


if __name__ == "__main__":
    main()
