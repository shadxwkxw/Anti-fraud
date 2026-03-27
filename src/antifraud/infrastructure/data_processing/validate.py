import argparse
import os

import pandas as pd


def validate_data(input_path):
    """
    Базовая проверка качества данных.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File {input_path} not found for validation")

    df = pd.read_csv(input_path)

    # Проверка на пустые значения
    null_count = df.isnull().sum().sum()
    if null_count > 0:
        print(f"Warning: {null_count} null values found")

    # Проверка обязательных колонок
    required_cols = ["Time", "Amount"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    print(f"Validation successful for {input_path}. Rows: {len(df)}")


def main():
    """CLI entrypoint for data validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    validate_data(args.input)


if __name__ == "__main__":
    main()
