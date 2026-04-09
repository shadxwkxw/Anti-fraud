import argparse
import os

import pandas as pd

from src.antifraud.infrastructure.storage.s3_io import s3_download


def validate_data(input_path):
    """
    Базовая проверка качества данных.
    """
    # Скачиваем из S3, если нет локально
    if not os.path.exists(input_path):
        s3_download(input_path, input_path)

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
