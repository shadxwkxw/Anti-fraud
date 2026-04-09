import argparse
import os

import pandas as pd

from src.antifraud.infrastructure.storage.postgres import init_db, save_batch_predictions
from src.antifraud.infrastructure.storage.s3_io import s3_download


def publish_results(input_path, execution_date):
    """
    Сохраняет результаты инференса в PostgreSQL (идемпотентно).
    """
    # Скачиваем из S3, если нет локально
    if not os.path.exists(input_path):
        s3_download(input_path, input_path)

    init_db()

    df = pd.read_csv(input_path)

    save_batch_predictions(df, execution_date)
    print(f"Successfully published {len(df)} predictions to Postgres")


def main():
    """CLI entrypoint for publishing batch predictions."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--date", required=True, help="Execution date (YYYY-MM-DD)")
    args = parser.parse_args()

    publish_results(args.input, args.date)


if __name__ == "__main__":
    main()
