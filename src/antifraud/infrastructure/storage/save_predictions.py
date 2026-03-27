import argparse
import os

import pandas as pd

from src.antifraud.infrastructure.storage.postgres import save_batch_predictions


def publish_results(input_path):
    """
    Сохраняет результаты инференса в PostgreSQL.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File {input_path} not found")

    df = pd.read_csv(input_path)

    # Сохраняем в БД
    save_batch_predictions(df)
    print(f"Successfully published {len(df)} predictions to Postgres")


def main():
    """CLI entrypoint for publishing batch predictions."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    publish_results(args.input)


if __name__ == "__main__":
    main()
