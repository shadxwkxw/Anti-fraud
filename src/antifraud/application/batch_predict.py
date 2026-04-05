import argparse
import os

import joblib

from src.antifraud.application.training.utils import load_and_preprocess_data
from src.antifraud.config import config


def run_batch(input_path, output_path=None):
    """
    Выполняет пакетное предсказание для данных из input_path.
    Сохраняет результат в файл. В БД не пишет — это делает save_results.
    """
    model_dir = config["storage"]["model_dir"]
    model_type = config["model"]["type"]

    model_path = os.path.join(model_dir, model_type, "model.joblib")
    scaler_path = os.path.join(model_dir, model_type, "scaler.joblib")

    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return None

    print(f"Loading model from {model_path}...")
    model = joblib.load(model_path)

    print(f"Loading data from {input_path}...")
    df = load_and_preprocess_data(input_path)

    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        df["Amount"] = scaler.transform(df[["Amount"]])

    features = df.copy()

    if "Class" in features.columns:
        features = features.drop("Class", axis=1)

    print("Running inference...")

    expected_features = model.feature_names_in_
    features = features[expected_features]

    print(f"Loaded {len(features)} transactions")

    probs = model.predict_proba(features)[:, 1]

    fraud_count = (probs > config["model"]["threshold"]).sum()
    print(f"Fraud detected: {fraud_count}")

    df["fraud_probability"] = probs
    df["is_fraud"] = probs > config["model"]["threshold"]

    if output_path:
        if output_path.endswith(".parquet"):
            df.to_parquet(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")

    return df


def main():
    """CLI entrypoint for batch inference."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    run_batch(args.input, args.output)
    print("Batch inference finished")


if __name__ == "__main__":
    main()
