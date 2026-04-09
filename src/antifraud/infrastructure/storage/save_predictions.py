import argparse
import os

import pandas as pd

from src.antifraud.infrastructure.storage.postgres import init_db, save_batch_predictions
from src.antifraud.infrastructure.storage.s3_io import s3_download


def publish_results(input_path):
    """
    Сохраняет результаты инференса в PostgreSQL.
    """
    # Скачиваем из S3, если нет локально
    if not os.path.exists(input_path):
        s3_download(input_path, input_path)

    init_db()

    df = pd.read_csv(input_path)

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
